FROM python:3.11-slim

# 디버깅 도구 및 필수 패키지 설치
RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg curl vim procps lsof && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app/source

# 다운로드 디렉토리 생성
RUN mkdir -p /app/downloads && \
    mkdir -p /app/downloads/status && \
    chmod -R 777 /app/downloads

# 환경 변수 설정
ENV PYTHONPATH=/app/source
ENV DOWNLOAD_DIR=/app/downloads
ENV PORT=5000
ENV HOST=0.0.0.0
ENV DEBUG=true
ENV PYTHONUNBUFFERED=1

# 시작 스크립트
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
