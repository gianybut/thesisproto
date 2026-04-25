# Pothole Detection Backend — API Reference

**Version:** 1.0  
**Base URL:** `http://localhost:5000/api`  
**Authentication:** Bearer token (user ID) in `Authorization` header

---

## Table of Contents

1. [Authentication](#authentication)
2. [Videos](#videos)
3. [Detections](#detections)
4. [Dashboard](#dashboard)
5. [Error Responses](#error-responses)
6. [Examples](#examples)

---

## Authentication

### POST /api/auth/login

Authenticate a user with username and password.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200 OK):**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "lgu_name": "Default LGU",
    "role": "admin",
    "created_at": "2026-04-24T10:00:00"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Invalid username or password"
}
```

---

### POST /api/auth/register

Register a new LGU user account.

**Request:**
```json
{
  "username": "inspector01",
  "password": "secure_password",
  "full_name": "Juan Dela Cruz",
  "lgu_name": "Makati City",
  "role": "inspector"
}
```

**Response (201 Created):**
```json
{
  "message": "Registration successful",
  "user": {
    "id": 2,
    "username": "inspector01",
    "full_name": "Juan Dela Cruz",
    "lgu_name": "Makati City",
    "role": "inspector",
    "created_at": "2026-04-24T10:30:00"
  }
}
```

**Error (409 Conflict):**
```json
{
  "error": "Username already exists"
}
```

---

### GET /api/auth/me

Get the currently authenticated user's information.

**Headers:**
```
Authorization: Bearer 1
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "full_name": "System Administrator",
    "lgu_name": "Default LGU",
    "role": "admin",
    "created_at": "2026-04-24T10:00:00"
  }
}
```

**Error (401 Unauthorized):**
```json
{
  "error": "Not authenticated"
}
```

---

### POST /api/auth/logout

Logout the current user (clears session).

**Headers:**
```
Authorization: Bearer 1
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## Videos

### POST /api/videos/upload

Upload a road survey video for pothole detection processing.

**Headers:**
```
Authorization: Bearer 1
Content-Type: multipart/form-data
```

**Form Data:**
- `video` (file, required) — Video file (MP4, AVI, MOV, MKV, WebM)

**Response (201 Created):**
```json
{
  "message": "Video uploaded successfully. Processing started.",
  "video": {
    "id": 5,
    "filename": "a1b2c3d4e5f6.mp4",
    "original_filename": "road_survey_v1.mp4",
    "file_size": 524288000,
    "duration": 600.5,
    "fps": 30.0,
    "resolution": "1920x1080",
    "status": "processing",
    "processing_progress": 0.0,
    "upload_date": "2026-04-24T11:00:00",
    "processed_date": null,
    "total_detections": 0,
    "user_id": 1
  }
}
```

**Error (400 Bad Request):**
```json
{
  "error": "No video file provided"
}
```

---

### GET /api/videos

List all videos for the authenticated user.

**Headers:**
```
Authorization: Bearer 1
```

**Response (200 OK):**
```json
{
  "videos": [
    {
      "id": 5,
      "filename": "a1b2c3d4e5f6.mp4",
      "original_filename": "road_survey_v1.mp4",
      "file_size": 524288000,
      "duration": 600.5,
      "fps": 30.0,
      "resolution": "1920x1080",
      "status": "completed",
      "processing_progress": 100.0,
      "upload_date": "2026-04-24T11:00:00",
      "processed_date": "2026-04-24T11:45:00",
      "total_detections": 23,
      "user_id": 1
    },
    {
      "id": 4,
      "filename": "x1y2z3a4b5c6.mp4",
      "original_filename": "road_survey_v2.mp4",
      "file_size": 312345600,
      "duration": 400.0,
      "fps": 24.0,
      "resolution": "1280x720",
      "status": "processing",
      "processing_progress": 45.0,
      "upload_date": "2026-04-24T10:30:00",
      "processed_date": null,
      "total_detections": 0,
      "user_id": 1
    }
  ]
}
```

---

### GET /api/videos/{video_id}

Get detailed information about a specific video including all its detections.

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID

**Response (200 OK):**
```json
{
  "video": {
    "id": 5,
    "filename": "a1b2c3d4e5f6.mp4",
    "original_filename": "road_survey_v1.mp4",
    "file_size": 524288000,
    "duration": 600.5,
    "fps": 30.0,
    "resolution": "1920x1080",
    "status": "completed",
    "processing_progress": 100.0,
    "upload_date": "2026-04-24T11:00:00",
    "processed_date": "2026-04-24T11:45:00",
    "total_detections": 23,
    "user_id": 1
  },
  "detections": [
    {
      "id": 145,
      "video_id": 5,
      "frame_number": 230,
      "timestamp": 7.667,
      "timestamp_formatted": "00:07.67",
      "confidence": 0.8923,
      "bbox": {
        "x1": 345.5,
        "y1": 220.3,
        "x2": 450.8,
        "y2": 310.2
      },
      "frame_snapshot": "snap_5_230.jpg"
    },
    {
      "id": 146,
      "video_id": 5,
      "frame_number": 425,
      "timestamp": 14.167,
      "timestamp_formatted": "00:14.17",
      "confidence": 0.7621,
      "bbox": {
        "x1": 500.2,
        "y1": 150.8,
        "x2": 600.5,
        "y2": 250.1
      },
      "frame_snapshot": "snap_5_425.jpg"
    }
  ]
}
```

---

### DELETE /api/videos/{video_id}

Delete a video and all associated data (original file, processed video, snapshots, detections).

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID

**Response (200 OK):**
```json
{
  "message": "Video deleted successfully"
}
```

**Error (404 Not Found):**
```json
{
  "error": "Video not found"
}
```

---

### GET /api/videos/{video_id}/stream

Stream the original uploaded video file.

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID

**Response:**
- Content-Type: `video/mp4`
- Body: Video file stream

---

### GET /api/videos/{video_id}/processed

Stream the processed video with bounding boxes drawn on detected potholes.

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID

**Response:**
- Content-Type: `video/mp4`
- Body: Annotated video file stream

---

### GET /api/videos/{video_id}/snapshot/{filename}

Retrieve a detection snapshot image.

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID
- `filename` (string, required) — Snapshot filename (e.g., `snap_5_230.jpg`)

**Response:**
- Content-Type: `image/jpeg`
- Body: JPEG image

---

## Detections

### GET /api/detections/{video_id}

Get all detection records for a specific video.

**Headers:**
```
Authorization: Bearer 1
```

**URL Parameters:**
- `video_id` (integer, required) — Video ID

**Response (200 OK):**
```json
{
  "video_id": 5,
  "total_detections": 23,
  "detections": [
    {
      "id": 145,
      "video_id": 5,
      "frame_number": 230,
      "timestamp": 7.667,
      "timestamp_formatted": "00:07.67",
      "confidence": 0.8923,
      "bbox": {
        "x1": 345.5,
        "y1": 220.3,
        "x2": 450.8,
        "y2": 310.2
      },
      "frame_snapshot": "snap_5_230.jpg"
    }
  ]
}
```

---

## Dashboard

### GET /api/dashboard/stats

Get aggregate statistics and recent activity for the authenticated user's dashboard.

**Headers:**
```
Authorization: Bearer 1
```

**Response (200 OK):**
```json
{
  "total_videos": 12,
  "completed_videos": 10,
  "processing_videos": 2,
  "total_detections": 156,
  "avg_confidence": 0.823,
  "total_duration": 3456.8,
  "recent_detections": [
    {
      "id": 156,
      "video_id": 6,
      "frame_number": 145,
      "timestamp": 4.833,
      "timestamp_formatted": "00:04.83",
      "confidence": 0.9045,
      "bbox": {
        "x1": 200.1,
        "y1": 100.5,
        "x2": 350.8,
        "y2": 280.3
      },
      "frame_snapshot": "snap_6_145.jpg"
    }
  ],
  "recent_videos": [
    {
      "id": 6,
      "filename": "p7q8r9s0t1u2.mp4",
      "original_filename": "latest_survey.mp4",
      "file_size": 156789012,
      "duration": 200.5,
      "fps": 24.0,
      "resolution": "1280x720",
      "status": "completed",
      "processing_progress": 100.0,
      "upload_date": "2026-04-24T14:00:00",
      "processed_date": "2026-04-24T14:15:00",
      "total_detections": 18,
      "user_id": 1
    }
  ]
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": "Error description"
}
```

### Common Error Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 400 | Bad Request | Missing required field, invalid file format |
| 401 | Unauthorized | Missing or invalid authentication token |
| 404 | Not Found | Video or resource doesn't exist |
| 409 | Conflict | Username already exists during registration |
| 500 | Server Error | Unexpected server error, check logs |

---

## Examples

### Example 1: Complete Upload & Detection Flow

```bash
# 1. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Response includes user ID = 1

# 2. Upload video
curl -X POST http://localhost:5000/api/videos/upload \
  -H "Authorization: Bearer 1" \
  -F "video=@road_survey.mp4"

# Response includes video ID = 5

# 3. Check processing status
curl -X GET http://localhost:5000/api/videos/5 \
  -H "Authorization: Bearer 1"

# 4. View dashboard stats
curl -X GET http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer 1"

# 5. Stream processed video
curl -X GET http://localhost:5000/api/videos/5/processed \
  -H "Authorization: Bearer 1" \
  -o annotated_video.mp4

# 6. Get detection at specific timestamp
curl -X GET http://localhost:5000/api/detections/5 \
  -H "Authorization: Bearer 1"
```

### Example 2: Create New User & Upload

```bash
# 1. Register new LGU inspector
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cebu_inspector",
    "password": "CebuRoads2026!",
    "full_name": "Maria Santos",
    "lgu_name": "Cebu City",
    "role": "inspector"
  }'

# Response includes new user ID = 2

# 2. Upload video as new user
curl -X POST http://localhost:5000/api/videos/upload \
  -H "Authorization: Bearer 2" \
  -F "video=@cebu_road_inspection.mp4"

# 3. Check stats
curl -X GET http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer 2"
```

### Example 3: Download Detection Snapshot

```bash
# Get a specific detection snapshot from video 5
curl -X GET "http://localhost:5000/api/videos/5/snapshot/snap_5_230.jpg" \
  -H "Authorization: Bearer 1" \
  -o pothole_detected_230.jpg
```

---

## Rate Limits

Currently, there are no rate limits. In production, implement:

- 100 requests per minute per user
- 5 concurrent uploads per user
- 1GB max stored video per user

---

## Versioning

API Version: **1.0**  
Last Updated: April 24, 2026

For updates and breaking changes, refer to the changelog.

---

## Support

For issues or questions:
1. Check the [Backend README](./README.md)
2. Review error logs in `backend/` folder
3. Check database state: `sqlite3 backend/pothole_detection.db`
