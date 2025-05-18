import yt_dlp
import os
import logging
import traceback
import subprocess
import time
import random
import hashlib
from .utils import sanitize_filename, extract_video_id

logger = logging.getLogger(__name__)

def check_dependencies():
    """필요한 의존성 도구 확인"""
    try:
        # yt-dlp 확인
        logger.debug("Checking yt-dlp dependency...")
        result = subprocess.run(['yt-dlp', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"yt-dlp check failed: {result.stderr.decode('utf-8', errors='replace')}")
            raise RuntimeError("yt-dlp가 설치되지 않았거나 실행할 수 없습니다.")
        else:
            version = result.stdout.decode('utf-8', errors='replace').strip()
            logger.debug(f"yt-dlp version: {version}")
        
        # ffmpeg 확인
        logger.debug("Checking ffmpeg dependency...")
        result = subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            logger.error(f"ffmpeg check failed: {result.stderr.decode('utf-8', errors='replace')}")
            raise RuntimeError("ffmpeg가 설치되지 않았거나 실행할 수 없습니다.")
        else:
            logger.debug("ffmpeg installed correctly")
            
    except FileNotFoundError as e:
        logger.error(f"Dependency not found: {str(e)}")
        raise RuntimeError(f"필수 도구를 찾을 수 없습니다: {str(e)}")

def download_audio(url, download_dir, quality='192'):
    """YouTube 비디오에서 오디오(MP3) 추출 함수"""
    # 의존성 확인
    logger.debug(f"Starting download process for URL: {url}")
    check_dependencies()
    
    os.makedirs(download_dir, exist_ok=True)
    logger.debug(f"Download directory: {download_dir}")
    
    # 비디오 ID 추출 (ID 기반 파일명 생성용)
    video_id = extract_video_id(url)
    if not video_id:
        logger.warning(f"Could not extract video ID from URL: {url}")
        # 해시 기반 임시 ID 생성
        video_id = hashlib.md5(url.encode()).hexdigest()[:11]
    
    logger.debug(f"Extracted video ID: {video_id}")
    
    # 다양한 User-Agent 목록
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.69',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0',
        'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0'
    ]
    
    # 최대 3번 시도
    for attempt in range(3):
        try:
            logger.info(f"Download attempt {attempt+1}/3...")
            
            # 재시도 간에 지연시간 추가
            if attempt > 0:
                wait_time = random.uniform(3, 7)
                logger.debug(f"Waiting for {wait_time:.1f} seconds before retry...")
                time.sleep(wait_time)
            
            # 매 시도마다 다른 User-Agent 사용
            user_agent = random.choice(user_agents)
            logger.debug(f"Using User-Agent: {user_agent}")
            
            def my_hook(d):
                if d['status'] == 'downloading':
                    percent = d.get('_percent_str', 'unknown')
                    speed = d.get('_speed_str', 'unknown')
                    eta = d.get('_eta_str', 'unknown')
                    logger.debug(f"다운로드 중: {percent} (속도: {speed}, 남은 시간: {eta})")
                    
                elif d['status'] == 'finished':
                    logger.info(f"다운로드 완료: {d['filename']}")
            
            logger.debug("Setting up yt-dlp options...")
            
            # 파일명 포맷 - 비디오 ID 기반 짧은 파일명 사용
            output_template = os.path.join(download_dir, f"{video_id}.%(ext)s")
            logger.debug(f"Using output template: {output_template}")
            
            # yt-dlp 옵션 설정
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': {
                    'default': output_template,  # 짧은 파일명 사용
                },
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
                'progress_hooks': [my_hook],
                'restrictfilenames': True,  # 안전한 파일명 사용
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'quiet': False,
                'no_warnings': False,
                'verbose': True,
                
                # 403 방지를 위한 옵션들
                'http_headers': {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Referer': 'https://www.youtube.com/',
                    'Connection': 'keep-alive',
                },
                'socket_timeout': 30,  # 타임아웃 증가
                'extractor_retries': 10,  # 추출 재시도 횟수
                'retries': 10,  # 다운로드 재시도 횟수
                'fragment_retries': 10,  # 조각 재시도 횟수
                'skip_download': False,
                'hls_prefer_native': False,
                'hls_use_mpegts': True,
                'external_downloader_args': ['-timeout', '30'],
                'call_home': False,
                'sleep_interval': 5,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 비디오 정보 가져오기
                logger.debug(f"Extracting info for URL: {url}")
                info_dict = ydl.extract_info(url, download=False)
                
                # 'entries' 키가 있다면 플레이리스트이므로 첫 번째 항목을 사용
                if 'entries' in info_dict:
                    logger.debug("Playlist detected, using first entry")
                    if not info_dict['entries']:
                        raise Exception("플레이리스트에 항목이 없습니다")
                    info_dict = info_dict['entries'][0]
                
                # 정보 추출
                title = info_dict.get('title', 'unknown')
                logger.debug(f"Title: {title}")
                logger.debug(f"ID: {info_dict.get('id', 'unknown')}")
                
                audio_info = {
                    'title': title,
                    'duration': info_dict.get('duration', 0),
                    'id': info_dict.get('id', 'unknown'),
                    'uploader': info_dict.get('uploader', 'unknown'),
                    'view_count': info_dict.get('view_count', 0),
                    'upload_date': info_dict.get('upload_date', 'unknown')
                }
                
                # 실제 다운로드 수행
                logger.info(f"Starting actual download for: {video_id} - {title}")
                ydl.download([url])
                
                # 예상 MP3 파일 경로
                expected_audio_path = os.path.join(download_dir, f"{video_id}.mp3")
                logger.debug(f"Expected audio path: {expected_audio_path}")
                
                # MP3 파일이 생성되었는지 확인
                if not os.path.exists(expected_audio_path):
                    logger.warning(f"Expected file not found: {expected_audio_path}")
                    
                    # 다운로드 디렉토리의 모든 파일 확인
                    all_files = os.listdir(download_dir)
                    logger.debug(f"All files in download directory: {all_files}")
                    
                    # 다른 이름의 MP3 파일 찾기
                    mp3_files = [f for f in all_files if f.endswith('.mp3')]
                    logger.debug(f"Available MP3 files: {mp3_files}")
                    
                    if mp3_files:
                        # 최근 생성된 MP3 파일 사용
                        mp3_files.sort(key=lambda x: os.path.getctime(os.path.join(download_dir, x)), reverse=True)
                        audio_path = os.path.join(download_dir, mp3_files[0])
                        logger.info(f"Using most recently created MP3 file: {audio_path}")
                    else:
                        # MP3로 변환되지 않은 다른 형식 찾기
                        other_files = [f for f in all_files if any(f.endswith(ext) for ext in ['.webm', '.m4a', '.opus'])]
                        
                        if other_files and attempt < 2:
                            logger.debug(f"Found other audio formats: {other_files}. Will retry.")
                            continue
                        elif attempt < 2:
                            continue  # 마지막 시도가 아니면 다시 시도
                        else:
                            raise Exception("MP3 파일이 생성되지 않았습니다")
                else:
                    audio_path = expected_audio_path
                
                # 추가 정보 업데이트
                audio_info['file_path'] = audio_path
                audio_info['file_size'] = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
                
                # 처리 성공 메시지
                logger.info(f"Successfully processed audio: {audio_path}")
                
                # 원본 제목과 파일 경로 매핑 저장 (필요시 참조용)
                with open(os.path.join(download_dir, f"{video_id}.info.txt"), 'w', encoding='utf-8') as f:
                    f.write(f"Title: {title}\nURL: {url}\nQuality: {quality}kbps\n")
                
                return audio_path, audio_info
                
        except Exception as e:
            logger.error(f"다운로드 시도 {attempt+1} 실패: {str(e)}")
            
            # 다음 시도에서 다른 설정 사용
            if attempt < 2:  # 마지막 시도가 아니라면
                logger.info("Retrying with different options...")
                continue
            else:
                logger.error(traceback.format_exc())
                raise Exception(f"오디오 다운로드 실패: {str(e)}")
    
    # 모든 시도가 실패한 경우
    raise Exception("모든 다운로드 시도 실패")
