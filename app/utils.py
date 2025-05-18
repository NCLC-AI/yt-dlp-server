import re
import logging

logger = logging.getLogger(__name__)

def validate_youtube_url(url):
    """
    유효한 YouTube URL인지 검사
    """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    return match is not None

def extract_video_id(url):
    """
    YouTube URL에서 비디오 ID 추출
    """
    video_id = None
    
    # youtu.be 형식 처리
    if 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    # youtube.com 형식 처리
    elif 'youtube.com' in url:
        if 'v=' in url:
            params = url.split('?')[1].split('&')
            for param in params:
                if param.startswith('v='):
                    video_id = param[2:]
                    break
        elif 'embed/' in url:
            video_id = url.split('embed/')[1].split('?')[0]
    
    return video_id

def format_duration(seconds):
    """
    초를 HH:MM:SS 형식으로 변환
    """
    if not seconds:
        return "00:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"

def format_file_size(size_bytes):
    """
    바이트를 읽기 쉬운 형식으로 변환 (KB, MB, GB)
    """
    if not size_bytes:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"