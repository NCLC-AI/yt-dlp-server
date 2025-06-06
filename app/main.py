from flask import Flask, request, jsonify, send_file, url_for
import os
import time
import logging
import traceback
from flask_cors import CORS
from .task_manager import TaskManager
from .downloader import start_download_task
from .utils import validate_youtube_url, format_duration, format_file_size

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/debug.log')  # 로그도 /tmp로 이동
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # CORS 허용

# 다운로드 경로를 /tmp 기반으로 변경
BASE_DOWNLOAD_DIR = '/tmp'
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

# 작업 관리자 초기화 (기본 디렉토리만 전달)
task_manager = TaskManager(BASE_DOWNLOAD_DIR)

def get_task_download_dir(task_id):
    """특정 작업의 다운로드 디렉토리 반환"""
    task_dir = os.path.join(BASE_DOWNLOAD_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)
    return task_dir

@app.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인 엔드포인트"""
    return jsonify({
        "status": "healthy", 
        "timestamp": time.time(),
    })

@app.route('/download/request', methods=['POST'])
def request_download():
    """YouTube 비디오 다운로드 요청 엔드포인트"""
    try:
        data = request.json
        logger.debug(f"Received download request: {data}")
        
        if not data or 'url' not in data:
            return jsonify({"error": "URL이 제공되지 않았습니다"}), 400
        
        url = data['url']
        quality = data.get('quality', '192')  # 기본 품질은 '192' (kbps)
        
        # URL 유효성 검사
        if not validate_youtube_url(url):
            logger.warning(f"Invalid YouTube URL: {url}")
            return jsonify({"error": "유효한 YouTube URL이 아닙니다"}), 400
        
        # 작업 생성
        task_id = task_manager.create_task(url, quality)
        logger.info(f"Created download task {task_id} for URL: {url}")
        
        # 작업별 다운로드 디렉토리 생성
        task_download_dir = get_task_download_dir(task_id)
        
        # 비동기 다운로드 시작 (작업별 디렉토리 사용)
        start_download_task(task_manager, task_id, url, task_download_dir, quality)
        
        # 응답 반환
        response = {
            "status": "accepted",
            "message": "다운로드 요청이 처리 중입니다",
            "task_id": task_id,
            "status_url": url_for('check_status', task_id=task_id, _external=True)
        }
        
        return jsonify(response), 202  # 202 Accepted
        
    except Exception as e:
        logger.error(f"다운로드 요청 처리 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/download/status/<task_id>', methods=['GET'])
def check_status(task_id):
    """다운로드 작업 상태 확인 엔드포인트"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
        
        # 기본 응답 데이터
        response = {
            "task_id": task_id,
            "status": task['status'],
            "progress": task['progress'],
            "created_at": task['created_at'],
            "updated_at": task['updated_at'],
        }
        
        # 상태에 따라 추가 정보 제공
        if task['status'] == 'completed':
            file_path = task.get('output_file')
            
            # 파일 정보 추가
            response.update({
                "title": task.get('title'),
                "duration": task.get('duration'),
                "duration_formatted": format_duration(task.get('duration')),
                "file_size": task.get('file_size'),
                "file_size_formatted": format_file_size(task.get('file_size')),
                "download_url": url_for('download_file', task_id=task_id, _external=True),
                "video_id": task.get('video_id'),
            })
            
        elif task['status'] == 'downloading':
            # 다운로드 진행 중인 경우 추가 정보
            response.update({
                "downloaded_bytes": task.get('downloaded_bytes', 0),
                "total_bytes": task.get('total_bytes', 0),
                "speed": task.get('speed', 0),
                "eta": task.get('eta', 0),
            })
            
        elif task['status'] == 'failed':
            # 실패한 경우 오류 메시지
            response["error"] = task.get('error')
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"상태 확인 처리 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/download/file/<task_id>', methods=['GET'])
def download_file(task_id):
    """완료된 파일 다운로드 엔드포인트"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
        
        if task['status'] != 'completed':
            return jsonify({
                "error": "파일이 아직 준비되지 않았습니다", 
                "status": task['status'],
                "progress": task['progress']
            }), 400
        
        file_path = task.get('output_file')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "파일을 찾을 수 없습니다"}), 404
        
        # 파일 다운로드 제공
        filename = os.path.basename(file_path)
        title = task.get('title', 'audio')
        
        # 제목을 파일명에 사용할 수 있도록 정리
        safe_title = title.replace('/', '_').replace('\\', '_').replace('?', '_')
        
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=f"{safe_title}.mp3"  # 다운로드시 보여줄 파일명
        )
        
    except Exception as e:
        logger.error(f"파일 다운로드 처리 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/download/delete/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """작업 및 관련 파일 삭제 엔드포인트"""
    try:
        success = task_manager.delete_task(task_id)
        
        if not success:
            return jsonify({"error": "작업을 찾을 수 없습니다"}), 404
        
        return jsonify({
            "status": "success",
            "message": f"작업 {task_id}가 삭제되었습니다"
        })
        
    except Exception as e:
        logger.error(f"작업 삭제 처리 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """모든 작업 목록 조회 엔드포인트"""
    try:
        tasks = task_manager.list_tasks()
        
        # 간략한 정보만 포함
        task_list = [{
            "task_id": task['id'],
            "status": task['status'],
            "progress": task['progress'],
            "created_at": task['created_at'],
            "updated_at": task['updated_at'],
            "title": task.get('title'),
            "video_id": task.get('video_id'),
            "url": task.get('youtube_url'),
        } for task in tasks]
        
        return jsonify({
            "total": len(task_list),
            "tasks": task_list
        })
        
    except Exception as e:
        logger.error(f"작업 목록 조회 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# 임시 파일 정리를 위한 엔드포인트 (옵션)
@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """오래된 임시 파일 정리"""
    try:
        import shutil
        import glob
        
        # 1시간 이상 된 디렉토리 찾기
        current_time = time.time()
        cleanup_count = 0
        
        for task_dir in glob.glob(os.path.join(BASE_DOWNLOAD_DIR, '*')):
            if os.path.isdir(task_dir):
                # 디렉토리 생성 시간 확인
                dir_mtime = os.path.getmtime(task_dir)
                if current_time - dir_mtime > 3600:  # 1시간 = 3600초
                    try:
                        shutil.rmtree(task_dir)
                        cleanup_count += 1
                        logger.info(f"Cleaned up old directory: {task_dir}")
                    except Exception as e:
                        logger.error(f"Failed to cleanup {task_dir}: {e}")
        
        return jsonify({
            "status": "success",
            "message": f"정리된 디렉토리 수: {cleanup_count}"
        })
        
    except Exception as e:
        logger.error(f"정리 작업 오류: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port}, debug mode: {debug}")
    logger.info(f"Base download directory: {BASE_DOWNLOAD_DIR}")
    app.run(host=host, port=port, debug=debug)
