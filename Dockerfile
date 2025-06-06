FROM python:3.11-slim

# 디버깅 도구 및 필수 패키지 설치
RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg curl vim procps lsof && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app/source

# /tmp 디렉토리 권한 설정 (이미 존재하지만 명시적으로)
RUN chmod 1777 /tmp

# 환경 변수 설정
ENV PYTHONPATH=/app/source
ENV PORT=5000
ENV HOST=0.0.0.0
ENV DEBUG=true
ENV PYTHONUNBUFFERED=1

# 시작 스크립트
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
