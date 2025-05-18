import os
import subprocess
import logging
import time
import hashlib
import threading
import yt_dlp
from .utils import extract_video_id

logger = logging.getLogger(__name__)

def get_ffmpeg_path():
    """시스템에서 FFmpeg 경로 찾기"""
    try:
        # 리눅스/macOS에서는 'which' 사용
        result = subprocess.run(['which', 'ffmpeg'], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
            
        # Windows에서는 'where' 사용
        result = subprocess.run(['where', 'ffmpeg'], 
                               capture_output=True, text=True, check=False)
        if result.returncode == 0:
            return result.stdout.strip().split('\n')[0]
    except Exception as e:
        logger.warning(f"FFmpeg path auto-detection failed: {str(e)}")
        
    # 도커 환경에서는 일반적인 경로
    if os.path.exists('/usr/bin/ffmpeg'):
        return '/usr/bin/ffmpeg'
    
    # 찾지 못한 경우
    return None

class ProgressHook:
    """다운로드 진행 상황 추적 훅"""
    
    def __init__(self, task_manager, task_id):
        self.task_manager = task_manager
        self.task_id = task_id
        self.start_time = None
        self.downloaded_bytes = 0
        self.total_bytes = 0
        
    def __call__(self, d):
        if d['status'] == 'downloading':
            if not self.start_time:
                self.start_time = time.time()
                
            self.downloaded_bytes = d.get('downloaded_bytes', 0)
            self.total_bytes = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            
            # 진행 상황 계산
            if self.total_bytes > 0:
                progress = int(100.0 * self.downloaded_bytes / self.total_bytes)
                
                # 속도 및 남은 시간
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                # 진행 상황 업데이트
                self.task_manager.update_task(
                    self.task_id,
                    status='downloading',
                    progress=progress,
                    downloaded_bytes=self.downloaded_bytes,
                    total_bytes=self.total_bytes,
                    speed=speed,
                    eta=eta
                )
            
        elif d['status'] == 'finished':
            # 다운로드 완료, 변환 시작
            self.task_manager.update_task(
                self.task_id,
                status='converting',
                progress=95,  # 95%로 표시 (변환 중)
                filename=d.get('filename', '')
            )
            
        elif d['status'] == 'error':
            # 오류 발생
            self.task_manager.update_task(
                self.task_id,
                status='failed',
                error=d.get('error', 'Unknown error during download')
            )

def download_audio_async(task_manager, task_id, url, download_dir, quality='192'):
    """
    비동기 방식으로 YouTube에서 오디오 다운로드
    별도 스레드에서 실행됨
    """
    try:
        task_manager.update_task(task_id, status='starting')
        
        # 비디오 ID 추출 (짧은 파일명을 위해)
        video_id = extract_video_id(url)
        if not video_id:
            video_id = hashlib.md5(url.encode()).hexdigest()[:11]
        
        # FFmpeg 경로 찾기
        ffmpeg_path = get_ffmpeg_path()
        
        # 파일명 설정
        filename = os.path.join(download_dir, video_id)
        
        # 진행 상황 훅 생성
        progress_hook = ProgressHook(task_manager, task_id)
        
        # 옵션 설정
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'outtmpl': f'{filename}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'noplaylist': True,
            'progress_hooks': [progress_hook],
            'quiet': False,
        }
        
        # FFmpeg 경로가 있으면 추가
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = ffmpeg_path
        
        # 다운로드 시도
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            title = info_dict.get('title', 'Unknown')
            duration = info_dict.get('duration', 0)
            
            # 실제 파일명 확인
            if info_dict.get('ext') == 'mp3':
                # 이미 MP3로 변환된 경우
                file_path = f"{filename}.mp3"
            else:
                # 다른 형식에서 변환된 경우
                file_path = ydl.prepare_filename(info_dict).replace('.webm', '.mp3')
                file_path = file_path.replace('.m4a', '.mp3')
            
            # 파일 존재 여부 확인
            if not os.path.exists(file_path):
                # 확장자가 다를 수 있으므로 인근 파일 찾기
                mp3_files = [
                    os.path.join(download_dir, f) for f in os.listdir(download_dir)
                    if f.startswith(video_id) and f.endswith('.mp3')
                ]
                if mp3_files:
                    file_path = mp3_files[0]
                else:
                    raise FileNotFoundError(f"MP3 file not found after download: {file_path}")
            
            # 메타데이터 저장
            with open(os.path.join(download_dir, f"{video_id}.info.txt"), 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\nAuthor: {info_dict.get('uploader', 'Unknown')}\nLength: {duration} seconds\nURL: {url}")
            
            # 작업 완료 업데이트
            task_manager.update_task(
                task_id,
                status='completed',
                progress=100,
                output_file=file_path,
                title=title,
                duration=duration,
                video_id=video_id,
                file_size=os.path.getsize(file_path) if os.path.exists(file_path) else 0
            )
            
    except Exception as e:
        logger.error(f"Error in download task {task_id}: {str(e)}", exc_info=True)
        task_manager.update_task(
            task_id,
            status='failed',
            error=str(e)
        )

def start_download_task(task_manager, task_id, url, download_dir, quality):
    """새 다운로드 작업 시작"""
    thread = threading.Thread(
        target=download_audio_async,
        args=(task_manager, task_id, url, download_dir, quality),
        daemon=True
    )
    thread.start()
    return task_id