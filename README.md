# YouTube Downloader API

A REST API service for downloading YouTube videos using yt-dlp.

## Features

- Download videos from YouTube
- Simple REST API interface
- Docker-based deployment

## Installation

### Prerequisites
- Docker
- Docker Compose

### Running with Docker Compose

1. Clone the repository
2. Run `docker-compose up -d`
3. Access the API at `http://localhost:5000`

> **Note:** This project now uses the `n8nai/yt-dlp-server:latest` Docker image.

## API Endpoints

### Download Request
```
POST /download/request
```
Initiates a download request for a YouTube video.

### Check Status
```
GET /download/status/<task_id>
```
Check the status of a download task.

### Download File
```
GET /download/file/<task_id>
```
Download the completed file.

### Delete Task
```
DELETE /download/delete/<task_id>
```
Delete a specific task.

### List Tasks
```
GET /tasks
```
List all download tasks.

## Testing

Test the API using curl:

```bash
# Initiate download
curl -X POST http://localhost:5000/download/request \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'

# Check status
curl http://localhost:5000/download/status/<task_id>

# Download file
curl -O http://localhost:5000/download/file/<task_id>

# List tasks
curl http://localhost:5000/tasks

# Delete task
curl -X DELETE http://localhost:5000/download/delete/<task_id>
```

## Troubleshooting

- Check container logs: `docker logs yt-dlp-server`
- Ensure proper network connectivity to YouTube

## License

MIT License