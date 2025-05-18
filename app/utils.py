import re
import unicodedata
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

def sanitize_filename(filename, max_length=50):
    """
    파일명에서 유효하지 않은 문자 제거 및 정리
    길이를 제한하여 파일명이 너무 길어지는 것을 방지
    
    Args:
        filename (str): 원본 파일명
        max_length (int): 최대 파일명 길이 (확장자 제외)
    
    Returns:
        str: 정리된 파일명
    """
    if not isinstance(filename, str):
        logger.warning(f"sanitize_filename received non-string: {type(filename)}")
        filename = str(filename)
        
    # 유니코드 정규화
    logger.debug(f"Sanitizing filename: {filename}")
    filename = unicodedata.normalize('NFKD', filename)
    
    # 파일명에 허용되지 않는 문자 제거
    clean_name = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # 공백 및 불필요한 문자 정리
    clean_name = re.sub(r'\s+', '_', clean_name)
    clean_name = re.sub(r'_{2,}', '_', clean_name)
    
    # 파일명 길이가 너무 길면 잘라내기
    if len(clean_name) > max_length:
        # 파일명을 적절히 자르고 해시 추가
        name_hash = hashlib.md5(clean_name.encode()).hexdigest()[:8]
        # 첫 부분(25자) + 해시(8자) + 하이픈
        clean_name = f"{clean_name[:max_length-9]}-{name_hash}"
        
    logger.debug(f"Sanitized result: {clean_name}")
    return clean_name

def validate_youtube_url(url):
    """
    유효한 YouTube URL인지 검사
    
    Args:
        url (str): 검사할 URL
    
    Returns:
        bool: 유효성 여부
    """
    logger.debug(f"Validating URL: {url}")
    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    
    match = re.match(youtube_regex, url)
    is_valid = match is not None
    logger.debug(f"URL validation result: {is_valid}")
    return is_valid

def extract_video_id(url):
    """
    YouTube URL에서 비디오 ID 추출
    
    Args:
        url (str): YouTube URL
    
    Returns:
        str: 비디오 ID 또는 None
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
