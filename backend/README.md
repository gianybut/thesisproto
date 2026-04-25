# Pothole Detection Backend API

Flask-based REST API for the Pothole Detection System. Handles video upload, processing, YOLOv8 inference, and detection storage.

## Features

- 🔐 User authentication (login/register for LGU personnel)
- 📹 Video upload & management
- 🤖 Real-time YOLOv8m pothole detection
- 📊 Dashboard statistics & detection retrieval
- 🎬 Processed video streaming with bounding boxes
- 💾 SQLite database with SQLAlchemy ORM

## Setup

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

Or for backend only:

```bash
pip install Flask==3.1.1 Flask-CORS==5.0.1 Flask-SQLAlchemy==3.1.1 \
    opencv-python ultralytics torch Pillow PyYAML
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional)
```

### 3. Run the Server

```bash
python run.py
```

Server will start at `http://localhost:5000`

## API Endpoints

### Authentication

- `POST /api/auth/login` — Login with username/password
- `POST /api/auth/register` — Register new LGU user
- `GET /api/auth/me` — Get current user info
- `POST /api/auth/logout` — Logout

### Videos

- `POST /api/videos/upload` — Upload video file
- `GET /api/videos` — List all user's videos
- `GET /api/videos/<id>` — Get video details with detections
- `DELETE /api/videos/<id>` — Delete video
- `GET /api/videos/<id>/stream` — Stream original video
- `GET /api/videos/<id>/processed` — Stream processed video with bounding boxes
- `GET /api/videos/<id>/snapshot/<filename>` — Get detection snapshot image

### Detections & Dashboard

- `GET /api/detections/<video_id>` — Get all detections for a video
- `GET /api/dashboard/stats` — Get user dashboard statistics

## Default Admin Account

After first run, a default admin user is created:

- **Username:** `admin`
- **Password:** `admin123`

⚠️ Change this password in production!

## Database Schema

### Users Table

```
- id (Integer, PK)
- username (String, unique)
- password_hash (String)
- full_name (String)
- lgu_name (String)
- role (String) — 'inspector' or 'admin'
- created_at (DateTime)
```

### Videos Table

```
- id (Integer, PK)
- filename (String) — UUID filename
- original_filename (String)
- file_size (Integer) — bytes
- duration (Float) — seconds
- fps (Float)
- resolution (String) — "1920x1080"
- status (String) — 'uploaded', 'processing', 'completed', 'failed'
- processing_progress (Float) — 0-100
- upload_date (DateTime)
- processed_date (DateTime)
- processed_filename (String)
- total_detections (Integer)
- user_id (Integer, FK to users)
```

### Detections Table

```
- id (Integer, PK)
- video_id (Integer, FK)
- frame_number (Integer)
- timestamp (Float) — seconds
- confidence (Float) — 0-1
- bbox_x1, bbox_y1, bbox_x2, bbox_y2 (Float) — bounding box coordinates
- frame_snapshot (String) — filename of snapshot image
- created_at (DateTime)
```

## Processing Pipeline

1. Video uploaded → stored in `uploads/` folder
2. Video metadata extracted (FPS, resolution, duration)
3. Processing starts in background thread
4. Frames extracted and passed to YOLOv8m model
5. Detections drawn on frames → `processed/` folder
6. Detection records saved to database
7. Snapshot images saved to `snapshots/` folder

## Configuration

### Upload Limits

- **Max file size:** 500MB (configured in `app.config`)
- **Supported formats:** MP4, AVI, MOV, MKV, WebM

### Model

- **Default model:** `ml/models/best.pt` (YOLOv8m trained on RDD2022 pothole dataset)
- **Fallback:** YOLOv8n pretrained (if custom model not found)
- **Confidence threshold:** 0.3 (configurable in `services/video_processor.py`)

## Development

### Project Structure

```
backend/
├── app.py                    # Flask app factory
├── models.py                 # SQLAlchemy database models
├── run.py                    # Development server entry point
├── requirements.txt          # Python dependencies
├── routes/
│   ├── auth.py              # Authentication endpoints
│   ├── videos.py            # Video management endpoints
│   └── detections.py        # Detection/stats endpoints
├── services/
│   └── video_processor.py   # YOLOv8 inference & video processing
├── uploads/                 # Uploaded video files
├── processed/               # Processed videos with annotations
├── snapshots/               # Detection snapshot images
└── pothole_detection.db     # SQLite database (auto-created)
```

### Testing Endpoints

```bash
# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Get current user
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer 1"

# Upload video
curl -X POST http://localhost:5000/api/videos/upload \
  -F "video=@sample.mp4" \
  -H "Authorization: Bearer 1"

# List videos
curl -X GET http://localhost:5000/api/videos \
  -H "Authorization: Bearer 1"

# Get dashboard stats
curl -X GET http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer 1"
```

## Troubleshooting

### Video processing fails

- Check that `ml/models/best.pt` exists
- Ensure OpenCV and ultralytics are installed: `pip install opencv-python ultralytics`
- Check `backend/` folder permissions for writing files

### FFmpeg not found

- Install ffmpeg for optimal video encoding
- On Windows: `choco install ffmpeg` or download from ffmpeg.org
- On Linux: `sudo apt-get install ffmpeg`
- On Mac: `brew install ffmpeg`

### Database errors

- Delete `pothole_detection.db` to reset database
- Ensure `backend/` folder is writable

### Port already in use

Change the port in `run.py`:

```python
app.run(debug=True, port=5001)  # Use different port
```

## Performance Notes

- Video processing happens asynchronously in background threads
- Frame skip optimization: processes ~5 frames per second for speed
- Large videos (>1GB) may take significant time to process
- GPU acceleration recommended for faster inference (requires CUDA-capable GPU)

## Future Improvements

- Token-based JWT authentication instead of sessions
- Batch video processing queue management
- WebSocket progress updates instead of polling
- Video caching & CDN support
- Mobile app API
- Multi-language support
