from flask import Flask, request, jsonify, send_file
import os
import time
import logging
import traceback  # 추가: 스택 트레이스 출력용
import json  # 추가: JSON 디버깅용
from flask_cors import CORS
from .downloader import download_audio, check_dependencies
from .utils import validate_youtube_url

# 더 자세한 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,  # INFO에서 DEBUG로 변경
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 콘솔 출력
        logging.FileHandler('/app/downloads/debug.log')  # 파일 출력
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # CORS 허용

# 다운로드 경로 설정
DOWNLOAD_DIR = os.environ.get('DOWNLOAD_DIR', '/app/downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.route('/health', methods=['GET'])
def health_check():
    """서버 상태 확인 엔드포인트"""
    try:
        # 의존성 확인
        check_dependencies()
        return jsonify({
            "status": "healthy", 
            "timestamp": time.time(),
            "dependencies": {
                "yt-dlp": "installed",
                "ffmpeg": "installed"
            }
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(traceback.format_exc())  # 추가: 스택 트레이스 출력
        return jsonify({
            "status": "unhealthy", 
            "error": str(e),
            "timestamp": time.time()
        }), 500

@app.route('/download/audio', methods=['POST'])
def audio_download():
    """YouTube 비디오에서 오디오(MP3) 추출 엔드포인트"""
    try:
        data = request.json
        logger.debug(f"Received request for URL: {data.get('url', 'no_url')}")
        
        if not data or 'url' not in data:
            return jsonify({"error": "URL이 제공되지 않았습니다"}), 400
        
        url = data['url']
        quality = data.get('quality', '192')  # 기본 품질은 '192' (kbps)
        
        logger.debug(f"Processing URL: {url}, quality: {quality}")
        
        # URL 유효성 검사
        if not validate_youtube_url(url):
            logger.warning(f"Invalid YouTube URL: {url}")
            return jsonify({"error": "유효한 YouTube URL이 아닙니다"}), 400
        
        logger.info(f"오디오 다운로드 요청: {url}")
        audio_path, audio_info = download_audio(url, DOWNLOAD_DIR, quality)
        
        # 안전하게 로깅
        logger.debug(f"Download result - path: {audio_path}")
        
        # 파일이 실제로 존재하는지 확인
        if not os.path.exists(audio_path):
            logger.error(f"File not found after download: {audio_path}")
            return jsonify({"error": "다운로드 후 파일을 찾을 수 없습니다"}), 500
            
        audio_filename = os.path.basename(audio_path)
        
        # 다운로드 정보 반환
        response = {
            "status": "success",
            "message": "오디오 다운로드 완료",
            "file_info": {
                "path": audio_path,
                "filename": audio_filename,
                "download_url": f"/files/{audio_filename}",
                "title": audio_info.get('title', '알 수 없는 제목'),
                "duration": audio_info.get('duration', 0),
                "filesize": os.path.getsize(audio_path),
                "format": "mp3",
                "quality": f"{quality}kbps",
                "video_id": audio_info.get('id', 'unknown')
            }
        }
        
        logger.debug(f"Sending response with status: {response['status']}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"오디오 다운로드 오류: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# 나머지 코드는 그대로...

if __name__ == '__main__':
    # 환경 변수에서 포트 가져오기, 기본값은 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port}, debug mode: {debug}")  # 추가: 서버 시작 로깅
    app.run(host=host, port=port, debug=debug)
