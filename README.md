[한국어](#korean) | [English](#english)

---

## Korean

GitHub에서 자동으로 소스 코드를 동기화하는 yt-dlp용 간단한 HTTP 서버 래퍼입니다.

### 기능

- 🚀 GitHub에서 자동 소스 코드 업데이트
- 📦 Docker 기반 배포
- 🔄 상태 모니터링
- 📁 영구 다운로드 저장소
- 🛠️ 간편한 설정
- 🌐 Standalone 또는 Reverse Proxy 지원

### 배포 옵션

이 프로젝트는 두 가지 배포 옵션을 제공합니다:

1. **Standalone 배포** (`docker-compose.yml`) - 직접 포트 노출
2. **Reverse Proxy 배포** (`docker-compose-traefik.yml`) - Traefik과 함께 사용

### 빠른 시작

#### 필수 요구사항

- Docker
- Docker Compose

#### Option 1: Standalone 배포

1. `docker-compose.yml` 파일을 다운로드합니다
2. 서비스를 실행합니다:

```bash
docker-compose up -d
```

3. `http://localhost:5000`에서 서비스에 접속합니다

#### Option 2: Reverse Proxy 배포 (Traefik)

1. `docker-compose-traefik.yml` 파일을 다운로드합니다
2. 기존 Traefik 네트워크 이름을 확인합니다:

```bash
docker network ls | grep traefik
```

3. `docker-compose-traefik.yml`에서 설정을 수정합니다:
   - `YOUR_YTDLP_DOMAIN`을 실제 도메인으로 변경
   - `traefik_network`를 실제 Traefik 네트워크 이름으로 변경
   - `mytlschallenge`를 실제 cert resolver 이름으로 변경 (필요시)

4. 서비스를 실행합니다:

```bash
docker-compose -f docker-compose-traefik.yml up -d
```

#### 상태 확인

- Standalone: `http://localhost:5000/health`
- Reverse Proxy: `https://YOUR_DOMAIN/health`

### 설정

#### 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `PORT` | `5000` | 서버 포트 |
| `DOWNLOAD_DIR` | `/app/downloads` | 다운로드 디렉토리 경로 |
| `DEBUG` | `true` | 디버그 모드 활성화 |

#### 커스텀 포트 (Standalone만 해당)

다른 포트에서 실행하려면 `docker-compose.yml`을 수정합니다:

```yaml
ports:
  - "8080:5000"  # 포트 8080에서 실행
```

#### 커스텀 다운로드 디렉토리

```yaml
volumes:
  - /path/to/your/downloads:/app/downloads  # 커스텀 다운로드 경로
```

### 사용법

#### 기본 명령어

```bash
# 서비스 시작 (Standalone)
docker-compose up -d

# 서비스 시작 (Traefik)
docker-compose -f docker-compose-traefik.yml up -d

# 로그 보기
docker-compose logs -f yt-dlp-server

# 서비스 중지
docker-compose down

# 최신 버전으로 업데이트
docker-compose pull
docker-compose up -d
```

#### API 엔드포인트

- `GET /health` - 상태 확인
- `POST /download` - 비디오 다운로드
- `GET /tasks` - 다운로드 작업 목록
- `GET /tasks/{task_id}` - 작업 상태 확인

### 문제 해결

#### 서비스가 시작되지 않을 때

1. 포트 충돌 확인 (Standalone):
   ```bash
   lsof -i :5000
   ```

2. 서비스 로그 확인:
   ```bash
   docker-compose logs yt-dlp-server
   ```

3. 네트워크 확인 (Traefik):
   ```bash
   docker network ls
   docker inspect <traefik_network_name>
   ```

#### 다운로드가 저장되지 않을 때

다운로드 디렉토리에 적절한 권한이 있는지 확인:
```bash
chmod 755 ./downloads
```

#### 소스 코드 업데이트

서비스는 시작 시 GitHub에서 자동으로 최신 코드를 가져옵니다. 강제로 업데이트하려면:

```bash
docker-compose restart git-cloner
docker-compose restart yt-dlp-server
```

### Traefik 설정 가이드

#### 네트워크 확인

기존 Traefik 설정에서 사용하는 네트워크를 확인하세요:

```bash
# 모든 네트워크 목록
docker network ls

# Traefik 컨테이너 네트워크 확인
docker inspect traefik_container_name | grep NetworkMode
```

일반적인 Traefik 네트워크 이름:
- `traefik_default`
- `proxy`
- `web`
- `traefik_traefik`

#### 도메인 설정

1. DNS에서 A 레코드 또는 CNAME 설정
2. `docker-compose-traefik.yml`에서 `YOUR_YTDLP_DOMAIN` 변경

#### SSL 인증서

Traefik의 기존 cert resolver를 사용하거나, 새로 설정:

```yaml
labels:
  - "traefik.http.routers.ytdlp.tls.certresolver=your-cert-resolver"
```

### 고급 설정

#### 프로덕션 배포

프로덕션 사용 시:

1. `DEBUG=false` 설정
2. 적절한 로깅 레벨 설정
3. 리소스 제한 설정
4. 모니터링 구성

#### 리소스 제한

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

---

## English

A simple HTTP server wrapper for yt-dlp with automatic GitHub source synchronization.

### Features

- 🚀 Automatic source code updates from GitHub
- 📦 Docker-based deployment
- 🔄 Health monitoring
- 📁 Persistent download storage
- 🛠️ Easy configuration
- 🌐 Standalone or Reverse Proxy support

### Deployment Options

This project provides two deployment options:

1. **Standalone Deployment** (`docker-compose.yml`) - Direct port exposure
2. **Reverse Proxy Deployment** (`docker-compose-traefik.yml`) - Use with Traefik

### Quick Start

#### Prerequisites

- Docker
- Docker Compose

#### Option 1: Standalone Deployment

1. Download the `docker-compose.yml` file
2. Run the service:

```bash
docker-compose up -d
```

3. Access the service at `http://localhost:5000`

#### Option 2: Reverse Proxy Deployment (Traefik)

1. Download the `docker-compose-traefik.yml` file
2. Check your existing Traefik network name:

```bash
docker network ls | grep traefik
```

3. Modify settings in `docker-compose-traefik.yml`:
   - Replace `YOUR_YTDLP_DOMAIN` with your actual domain
   - Replace `traefik_network` with your actual Traefik network name
   - Replace `mytlschallenge` with your cert resolver name (if needed)

4. Run the service:

```bash
docker-compose -f docker-compose-traefik.yml up -d
```

#### Health Check

- Standalone: `http://localhost:5000/health`
- Reverse Proxy: `https://YOUR_DOMAIN/health`

### Configuration

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `5000` | Server port |
| `DOWNLOAD_DIR` | `/app/downloads` | Download directory path |
| `DEBUG` | `true` | Enable debug mode |

#### Custom Port (Standalone only)

To run on a different port, modify the `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Run on port 8080
```

#### Custom Download Directory

```yaml
volumes:
  - /path/to/your/downloads:/app/downloads  # Custom download path
```

### Usage

#### Basic Commands

```bash
# Start service (Standalone)
docker-compose up -d

# Start service (Traefik)
docker-compose -f docker-compose-traefik.yml up -d

# View logs
docker-compose logs -f yt-dlp-server

# Stop service
docker-compose down

# Update to latest version
docker-compose pull
docker-compose up -d
```

#### API Endpoints

- `GET /health` - Health check
- `POST /download` - Download videos
- `GET /tasks` - List download tasks
- `GET /tasks/{task_id}` - Get task status

### Troubleshooting

#### Service won't start

1. Check port conflicts (Standalone):
   ```bash
   lsof -i :5000
   ```

2. View service logs:
   ```bash
   docker-compose logs yt-dlp-server
   ```

3. Check network (Traefik):
   ```bash
   docker network ls
   docker inspect <traefik_network_name>
   ```

#### Downloads not persisting

Ensure the downloads directory has proper permissions:
```bash
chmod 755 ./downloads
```

#### Update source code

The service automatically pulls the latest code from GitHub on startup. To force an update:

```bash
docker-compose restart git-cloner
docker-compose restart yt-dlp-server
```

### Traefik Configuration Guide

#### Network Check

Check the network used by your existing Traefik setup:

```bash
# List all networks
docker network ls

# Check Traefik container network
docker inspect traefik_container_name | grep NetworkMode
```

Common Traefik network names:
- `traefik_default`
- `proxy`
- `web`
- `traefik_traefik`

#### Domain Setup

1. Set up A record or CNAME in DNS
2. Replace `YOUR_YTDLP_DOMAIN` in `docker-compose-traefik.yml`

#### SSL Certificates

Use your existing Traefik cert resolver or set up a new one:

```yaml
labels:
  - "traefik.http.routers.ytdlp.tls.certresolver=your-cert-resolver"
```

### Advanced Configuration

#### Production Deployment

For production use:

1. Set `DEBUG=false`
2. Configure appropriate logging levels
3. Set resource limits
4. Set up monitoring

#### Resource Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

---

## License / 라이선스

This project follows the same license as the original yt-dlp-server repository.
이 프로젝트는 원본 yt-dlp-server 저장소와 동일한 라이선스를 따릅니다.

## Contributing / 기여

Issues and pull requests are welcome!
이슈와 풀 리퀘스트를 환영합니다!