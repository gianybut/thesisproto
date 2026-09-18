# Bantay Kalsada System Overview

This document gives a single, current overview of the road damage detection system in this workspace. It reflects the codebase as it actually runs, not the older summaries that describe an earlier pothole-only version.

## What The System Is

Bantay Kalsada is a road damage detection platform for Philippine LGUs. Users upload road survey videos, the backend runs YOLO-based detection on the footage, detections are stored in SQLite, and the frontend presents the results through a React web app with role-based navigation.

The product is focused on the four CRDDC 2022 / RDD2022 damage classes:

- `D00` longitudinal crack
- `D10` transverse crack
- `D20` alligator crack
- `D40` pothole

There is no `D30` in the current classification scheme. Severity scoring is not part of the app anymore and is intentionally left inactive.

## High-Level Architecture

The repository has three main parts:

1. `backend/` - Flask API, SQLite persistence, video processing, geolocation, and report endpoints.
2. `frontend/` - React + Vite single-page app for login, upload, dashboards, video browsing, georeferencing, and map views.
3. `ml/` - Offline training and dataset preparation scripts for the YOLO model; the backend only consumes the trained model artifact at `ml/models/best.pt`.

The backend and frontend are launched separately. The launch scripts in the repo root handle the correct working directories.

## Core User Flow

1. A user logs in with a simple token scheme based on the user ID.
2. The user uploads a road survey video, optionally with a GPS track.
3. The backend saves the upload and extracts metadata such as duration, FPS, and resolution.
4. A background thread runs video inference frame-by-frame.
5. Detections are written to the database and snapshots are saved.
6. If GPS data exists, detections are positioned from the GPS track. Otherwise, the user can georeference the video with manual control points.
7. The frontend displays the processed video, detection list, dashboard stats, database views, and map views.

## Backend Behavior

The backend is a Flask application built around SQLAlchemy and SQLite.

- `backend/app.py` creates the app, registers blueprints, ensures storage folders exist, and initializes the database.
- `backend/routes/` contains the API areas for auth, uploads, detections, damage map, public reports, database views, and accounts.
- `backend/services/video_processor.py` contains the inference pipeline and video re-encoding flow.
- `backend/services/gps_service.py` and `backend/services/georeference_service.py` handle coordinate placement.

Important runtime details:

- Video processing runs in a plain Python thread, not a queue or worker process.
- If the backend restarts while a video is still `uploaded` or `processing`, that work is lost and the app marks the video as failed on startup.
- Output videos are written as AVI first, then re-encoded to H.264 MP4 with `ffmpeg` if it is available on PATH.
- The backend enforces a 10-minute video limit and a 500 MB upload limit.

## Authentication And Roles

Authentication is intentionally simple: `Authorization: Bearer <user.id>` is treated as the token. There is no signature, expiry, or real token verification. In practice, the backend parses the user ID and uses it as the identity.

Role handling is mostly client-side:

- The frontend controls which routes and navigation entries are visible.
- The backend only performs strict role enforcement in a few places, mainly the admin accounts routes.

The active frontend role set is:

- `barangay`
- `municipal`
- `provincial`
- `admin`

Unknown roles fall back to the most restrictive access level.

## Database And Migration Model

The app uses SQLite at `backend/pothole_detection.db`.

The schema is created with `db.create_all()`, which creates missing tables but does not alter existing ones. Because of that, any new column added to `models.py` must also be listed in `backend/migrate.py`.

The migration script is idempotent and can be run repeatedly. It is also now invoked during backend startup so older databases can self-heal before ORM queries run.

Key models:

- `User`
- `Video`
- `Detection`
- `GpsTrackPoint`
- `RouteControlPoint`
- `PublicReport`

## Video And Detection Pipeline

Uploads are stored first, then processed asynchronously.

- Metadata is extracted with OpenCV.
- Inference runs on sampled frames instead of every single frame.
- Detections are deduplicated so repeated sightings across nearby frames do not become duplicate rows.
- Each detection stores bounding boxes, timestamps, confidence, and a snapshot image path.

Positioning can happen in two ways:

- `gps_file` - coordinates come from an uploaded GPS track.
- `georeferenced` - coordinates come from manually placed control points.
- `none` - the detection has no coordinates yet.

## Frontend Behavior

The frontend is a React + Vite app that talks to the Flask API directly.

Main pages currently include:

- Login
- Dashboard
- Upload
- Video list
- Detection viewer
- Georeference view
- Damage map
- Database views

Styling is centralized in `frontend/src/index.css`, and the app uses a single API client in `frontend/src/api.js`.

## Operational Notes

- The backend expects `ffmpeg` for browser-playable processed video output.
- The default admin account is created automatically on first boot if no users exist.
- The system is designed to be run from the repository root.
- `start_backend.bat` and `start_backend.sh` handle backend startup.
- `start_frontend.bat` and `start_frontend.sh` handle frontend startup.

Recommended commands from the repo root:

```bash
python backend/migrate.py
```

```bash
start_backend.bat
```

```bash
start_frontend.bat
```

## Important Constraints

There are a few design decisions to keep in mind when modifying the system:

- Severity scoring is deprecated and should not be wired back in without an explicit decision.
- The current shipped model is still a single-class pothole model, so classification quality depends on the current `best.pt` artifact.
- The map and geolocation features depend on either uploaded GPS data or manual control points; there is no automatic clamping outside the georeferenced range.
- Some older README files still describe an earlier, simpler version of the app, so the code is the source of truth.

## Where To Look Next

If you want implementation detail, the most useful files are:

- `backend/app.py`
- `backend/models.py`
- `backend/migrate.py`
- `backend/services/video_processor.py`
- `backend/services/gps_service.py`
- `backend/services/georeference_service.py`
- `frontend/src/App.jsx`
- `frontend/src/api.js`
- `frontend/src/pages/`
