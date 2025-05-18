# YouTube to MP3 Downloader API

A REST API service for downloading and converting YouTube videos to MP3 format.

## Features

- Extract high-quality MP3 audio from YouTube URLs
- Docker-based deployment for consistent operation across environments (Windows/GCP)
- File management capabilities (listing, downloading, deleting)
- Simple REST API interface
- Integration-ready for n8n workflows

## Installation

### Prerequisites
- Docker
- Docker Compose

### Running with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd youtube-mp3-api
```

2. Start the service:
```bash
docker-compose up -d
```

3. Check the service status:
```bash
curl http://localhost:5000/health
```

## API Endpoints

### Health Check
```
GET /health
```
Returns the current service status and dependency information.

### Download Audio as MP3
```
POST /download/audio
```
Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "192"  // Optional: Audio quality in kbps (default: 192)
}
```
Response:
```json
{
  "status": "success",
  "message": "Audio download complete",
  "file_info": {
    "path": "/app/downloads/Video_Title.mp3",
    "filename": "Video_Title.mp3",
    "download_url": "/files/Video_Title.mp3",
    "title": "Original Video Title",
    "duration": 180,
    "filesize": 3456789,
    "format": "mp3",
    "quality": "192kbps"
  }
}
```

### List Files
```
GET /list
```
Returns a list of all downloaded files.

### Download File
```
GET /files/{filename}
```
Downloads the specified file.

### Delete File
```
DELETE /delete/{filename}
```
Deletes the specified file.

### Purge All Files
```
POST /purge
```
Deletes all downloaded files.

## Deployment Instructions

### Windows Deployment
1. Install Docker Desktop
2. Navigate to the project directory
3. Run `docker-compose up -d`
4. Access the API at `http://localhost:5000`

### GCP Deployment
1. Create a Compute Engine VM instance
2. Install Docker and Docker Compose:
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.18.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```
3. Copy the project files to the VM
4. Run `docker-compose up -d`
5. Open firewall port 5000:
   ```bash
   gcloud compute firewall-rules create allow-youtube-api --allow tcp:5000
   ```
6. Access the API at `http://<vm-external-ip>:5000`

## Integration with n8n

The API can be easily integrated with n8n workflows:

1. Add an HTTP Request node
2. Set Method to POST
3. Set URL to `http://your-server:5000/download/audio`
4. Add JSON Body:
   ```json
   {
     "url": "{{$node["Previous_Node"].json["youtube_url"]}}",
     "quality": "192"
   }
   ```
5. Process the response - the downloaded file is available at the URL in `file_info.download_url`

## Testing

Test the API using curl:

```bash
# Health check
curl http://localhost:5000/health

# Download MP3
curl -X POST http://localhost:5000/download/audio \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=dQw4w9WgXcQ", "quality":"192"}'

# List files
curl http://localhost:5000/list

# Download file
curl -O http://localhost:5000/files/FILENAME.mp3

# Delete file
curl -X DELETE http://localhost:5000/delete/FILENAME.mp3
```

## Troubleshooting

- **Permission Issues**: Ensure the container has proper permissions to write to the download directory
- **Missing Dependencies**: Check `/health` endpoint to verify yt-dlp and ffmpeg are properly installed
- **YouTube Restrictions**: Some videos may have download restrictions or region limitations

## Technical Details

- Built with Flask, yt-dlp, and FFmpeg
- Uses Python 3.11 as the base image
- Includes automatic error handling and detailed logging
- All files are stored in a Docker volume for persistence

## License

MIT License