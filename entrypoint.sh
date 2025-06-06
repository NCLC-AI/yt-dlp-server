#!/bin/bash
set -e

# requirements.txt가 있으면 패키지 설치
if [ -f "requirements.txt" ]; then
    echo "Installing Python packages..."
    pip install --no-cache-dir -r requirements.txt
fi

# 애플리케이션 실행
exec python -m app.main
