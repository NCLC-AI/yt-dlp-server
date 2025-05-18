FROM python:3.11-slim

WORKDIR /app

# 디버깅 도구 및 필수 패키지 설치
RUN apt-get update --fix-missing && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ffmpeg curl vim procps lsof && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# 필요한 파이썬 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 앱 코드 복사
COPY ./app /app/app

# 다운로드 디렉토리 생성
RUN mkdir -p /app/downloads && \
    mkdir -p /app/downloads/status && \
    chmod -R 777 /app/downloads
VOLUME /app/downloads

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV DOWNLOAD_DIR=/app/downloads
ENV PORT=5000
ENV HOST=0.0.0.0
ENV DEBUG=true
ENV PYTHONUNBUFFERED=1

# 서버 실행
CMD ["python", "-m", "app.main"]

# 포트 노출
EXPOSE 5000