# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"Bantay Kalsada" — a road damage detection system for Philippine LGUs. A YOLOv8 model scores road
survey videos for the four CRDDC 2022 classes (D00 longitudinal, D10 transverse, D20 alligator,
D40 pothole — RDD2022's own codes; there is no D30), detections are geo-located from an uploaded
GPS track or from user-placed control points, and surfaced through a React web app with LGU roles
(barangay → municipal → provincial → admin). The partner office is the Local Government Unit of
Mendez-Nuñez, Cavite (the seeded admin's `lgu_name`); never "DPWH Central Office". Severity
scoring was dropped from the product: nothing computes, stores, returns or displays it.

Four independent parts: [backend/](backend/) (Flask API), [frontend/](frontend/) (React + Vite),
[ml/](ml/) (dataset prep + YOLO training, offline — the backend only consumes the resulting
`ml/models/best.pt`), and [mobile/](mobile/) (Expo capture app for iPhone and Android: records video + a
GPX on one phone and posts both to the unchanged `/api/videos/upload`; capture only, no on-device
inference). The team captures survey data on iPhones. Platform differences (screen lock, GPS rate,
`.mov` vs `.mp4`, upload transport) are tabled in [mobile/README.md](mobile/README.md) and all
platform branches live in `mobile/src/platform.js` / `mobile/src/api.js` — keep them there and keep
that table current.

## Commands

Run everything from the repo root. The launcher scripts `cd` into the right subdirectory themselves.

```bash
# One-time setup
python -m venv .venv && .venv\Scripts\activate   # Windows; source .venv/bin/activate elsewhere
pip install -r requirements.txt
cd frontend && npm install && cd ..
python backend/migrate.py                        # after pulling: adds any columns an existing DB lacks

# Run (two terminals)
start_backend.bat      /  ./start_backend.sh      # Flask on :5000
start_frontend.bat     /  ./start_frontend.sh     # Vite on :5173

# Manual equivalents
python backend/run.py
cd frontend && npm run dev

# Frontend
npm run lint      # eslint
npm run build

# Mobile (needs a development build, not Expo Go — see mobile/README.md)
cd mobile && npm install && npx expo run:ios --device    # or: npx expo run:android
npx expo lint
```

Login: `admin` / `admin123` (auto-created on first boot if the users table is empty). `python backend/test_api.py`
logs in and uses the returned token.

**Windows:** `start_backend.bat` sets `PYTHONUTF8=1`. The backend logs heavily with emoji; without
it, `print()` raises `UnicodeEncodeError` under cp1252. Set it if you launch Python directly.

### Tests

There is no test suite. [backend/test_api.py](backend/test_api.py) is a manual smoke script that
hits a *running* server (`python backend/test_api.py`) and needs `requests`, which is **not** in
[requirements.txt](requirements.txt) — `pip install requests` first.

### ML scripts

Run manually with `ml/` as the working directory. They are not wired into the app.

```bash
cd ml
python download_rdd2022.py     # fetch RDD2022, keep the four classes, cap per class (RDD_MAX_PER_CLASS), emit ./pothole_dataset
python dataset_prep.py --local <extracted> --max-per-class 2500   # same from a manual download (VOC XML)
python convert_rdd2022.py      # alternative: dataset-ninja/Supervisely JSON → YOLO
python train_local.py          # YOLOv8m, 150 epochs, imgsz 1024, batch 4 (tuned for 8GB VRAM)
python train_model.py --model yolov8m --epochs 100 --patience 20   # thesis defaults; prints per-class AP@50
python evaluate_model.py
```

Training writes to `ml/pothole_training/...`; copy the winning `weights/best.pt` to
`ml/models/best.pt` — that is the path the backend loads. Datasets and run artifacts are gitignored.

## Architecture

### Auth: signed tokens, one middleware

`POST /api/auth/login` returns `token` (HS256 JWT, `sub` = user id, expiry `JWT_EXPIRY_HOURS`,
default 12) plus `user`. [backend/auth_tokens.py](backend/auth_tokens.py) registers a
`before_request` hook: every `/api/*` request needs `Authorization: Bearer <jwt>` for an existing,
`active` user, or it gets a 401 with `code` = `token_missing` / `token_expired` / `token_invalid` /
`user_inactive` before the route runs. Exceptions are the endpoint names in `PUBLIC_ENDPOINTS`
(login, logout, register, anonymous report submission). The media endpoints in
`QUERY_TOKEN_ENDPOINTS` also accept `?token=`, because `<video>`/`<img>` cannot send headers.
There is no Flask session and no server-side logout; a token is valid until it expires.

The signing key is `SECRET_KEY` from the environment, else a random key generated into the
gitignored `backend/.secret_key` on first boot. Deleting that file logs everyone out.

Routes read the caller with `current_user_id()` / `current_user()` from `auth_tokens` (most route
files import it as `get_user_id`). A new route is protected by default; add its endpoint name to
`PUBLIC_ENDPOINTS` only if it must work logged out.

What is still true:

- **Role enforcement is almost entirely client-side.** `ROLE_ROUTE_ACCESS` in
  [frontend/src/App.jsx](frontend/src/App.jsx) hides routes; the only server-side role check is
  `_require_admin()` in [backend/routes/accounts.py](backend/routes/accounts.py).
- **Data scoping varies per route file, not through a shared layer.** `videos`, `detections`, and
  `dashboard/stats` filter by `Video.user_id`; `map`, `database`, and `reports` return everything to
  any logged-in caller.

The web client keeps the token in `localStorage` (`token`); [api.js](frontend/src/api.js) attaches it,
appends it to media URLs, and on any 401 outside login clears it and fires `auth:expired`, which
`App.jsx` turns into the login screen with a notice.

### Role list drift

The frontend knows four roles — `barangay`, `municipal`, `provincial`, `admin` — in
`ROLE_ROUTE_ACCESS` ([App.jsx](frontend/src/App.jsx)) and `ROLE_NAV` + `ROLE_LABELS`
([Navbar.jsx](frontend/src/components/Navbar.jsx)); the two tables duplicate each other and must stay
in sync. Unknown roles fall back to `barangay` (the most restrictive set).

The backend still carries the older, wider list: `models.VALID_ROLES` has `public`,
`auth.SELF_REGISTER_ROLES` has `public`/`inspector`, and `/api/auth/register` plus `/api/accounts/*`
are still live although their UI was removed. Accounts are meant to be created directly in the
database; backend cleanup of these routes is pending and is the user's own workstream.

### Video processing pipeline

[backend/routes/videos.py](backend/routes/videos.py) saves the upload, pulls metadata with OpenCV,
then spawns a bare `threading.Thread` running
[backend/services/video_processor.py](backend/services/video_processor.py). No queue, no worker
process — processing dies with the server and does not survive a restart; `create_app()` marks any
video still `uploaded`/`processing` as `failed` on boot so nothing spins forever. Uploads longer than
`MAX_VIDEO_DURATION_S` (600 s) are rejected with 400 before a thread is spawned. Progress is written
to `Video.processing_progress` every 30 frames and the frontend polls for it.
`GET /api/videos/export` returns per-video frames / sampled frames / processing seconds — the
throughput data for the thesis evaluation chapter.

Inside `_run_detection_pipeline`:

- Inference runs on every `fps/INFERENCE_FPS`-th frame at `CONF_THRESHOLD` / `IOU_THRESHOLD` — module
  constants at the top of `video_processor.py` that the thesis cites; change them there only. Between
  inference frames the last boxes are re-drawn for `fps*0.5` frames so the annotated video does not flicker.
- Detections are deduplicated by a `(100px grid cell, frame // (fps*2))` key, so one pothole seen
  across consecutive frames yields one row.
- `_classify_damage` maps model class names to RDD2022 codes (D00/D10/D20/D40) by substring, then
  falls back to class index in the `ml/dataset_prep.py` order, then to `D40`. The shipped `best.pt`
  is **still single-class** (`nc: 1`, name `pothole`) — retraining on four classes is the open
  critical-path task; until it lands everything becomes D40.
- Video output is written as **MJPG AVI via OpenCV** (fast), then re-encoded to H.264 MP4 with a
  shelled-out `ffmpeg` (`-crf 18`) for browser playback. Without ffmpeg on PATH the AVI is kept and
  most browsers will not play it. `processed_filename` records whatever survived, so read it rather
  than assuming an extension.

### Severity scoring (dropped)

Nothing in the app computes, filters, sorts, exports or shows severity. `Detection.severity` /
`severity_score` remain as columns only so existing databases need no destructive migration; they
are not in `to_dict()`, `migrate.py` nulls any legacy values, and no route reads them.
[backend/services/severity_service.py](backend/services/severity_service.py) is kept for reference
(thesis Sec 3.1.6 future work: `0.4×damageType + 0.3×bboxArea + 0.2×cluster + 0.1×confidence`) and
has no callers. Do not wire it back in without a decision.

### GPS synchronization

An optional `.gpx`/`.csv` is uploaded alongside the video; `time_offset` (seconds) aligns track
start to video start. [backend/services/gps_service.py](backend/services/gps_service.py) normalizes
track timestamps to seconds-from-start, stores every point as a `GpsTrackPoint`, and
`interpolate_gps()` linearly interpolates a coordinate for each detection's `frame_number / fps`.
No GPS file means `latitude`/`longitude` stay `NULL` until the user places control points on
`/videos/:id/georeference`; [backend/services/georeference_service.py](backend/services/georeference_service.py)
then interpolates piecewise between the bracketing points and returns nothing outside their range
(it never clamps, unlike `interpolate_gps`). `position_source` on both `Video` and `Detection` records
which path positioned each row: `gps_file`, `georeferenced`, or `none`. `GET /api/map/gps-tracks`
returns one route per survey: the full track for a GPS-file survey, or the straight segments between
control points (`source: control_points`) for a hand-placed one. `Kyle.gpx` at the repo root is a
sample track.

### Database

SQLite at `backend/pothole_detection.db`, created by `db.create_all()` in `create_app()`.
`create_all()` creates new tables but never alters existing ones, so every column added after a DB
exists must be listed in [backend/migrate.py](backend/migrate.py); run `python backend/migrate.py`
(idempotent) after pulling, or delete the gitignored DB. The same script remaps rows written under the
old D10/D20/D30 code scheme. [backend/purge_uploads.py](backend/purge_uploads.py) deletes raw uploads
past the retention period (dry-run unless `--apply`).

Models ([backend/models.py](backend/models.py)): `User`, `Video`, `Detection`, `GpsTrackPoint`,
`RouteControlPoint`, `PublicReport`. `Detection` is the central record, carrying both AI output (bbox, confidence, damage
type) and workflow state (`inspection_status`, `repair_status`). Validated
`PublicReport`s are promoted into `Detection` rows with `source_type='public_report'`, which is why
the database and map views mix both sources.

### Adding an API area

1. New blueprint in `backend/routes/`, registered with its `url_prefix` in
   [backend/app.py](backend/app.py) (`create_app` also creates the upload/processed/snapshot/report
   folders — add any new one there).
2. New client group in [frontend/src/api.js](frontend/src/api.js).
3. New page in `frontend/src/pages/`, plus a `<Route>` in `App.jsx`, an entry in `NAV_ITEMS`, and
   the path added to both `ROLE_ROUTE_ACCESS` and `ROLE_NAV`.

### Frontend conventions

The Vite dev server talks to `http://localhost:5000/api`, hard-coded in `api.js` — there is no proxy
and no env var, so changing the backend port means editing that constant. All styling lives in one
global [frontend/src/index.css](frontend/src/index.css), built against
[frontend/design.md](frontend/design.md) — the authority on every visual decision: seven colour
tokens (no eighth), Newsreader / Archivo / IBM Plex Mono, 1px `--rule` borders, no shadows,
gradients, emoji or badge pills, mono for every database number. A clearly marked TRANSITIONAL
block at the end of the file styles classes on pages not yet rebuilt; delete rules from it as pages
migrate. There are no CSS modules or component-scoped styles. Pages are plain function components
using `useState`/`useEffect` polling — no state library, no data-fetching library.

The map page ([DamageMapPage.jsx](frontend/src/pages/DamageMapPage.jsx)) is deliberately plain:
OpenStreetMap tiles, one solid route per survey with labelled Start/End markers, and one
`CircleMarker` dot per detection coloured by damage class. The four class colours (`DAMAGE_CLASSES`
at the top of that file) are the only colours in the app outside the seven tokens — they encode data
and are used nowhere else. No heatmap, no clustering: `leaflet.markercluster` is a dependency but must
stay unused.

## Documentation in the repo

[README.md](README.md), [backend/README.md](backend/README.md), and
[backend/API_REFERENCE.md](backend/API_REFERENCE.md) predate the GPS, map, public-report, database,
and accounts features — they describe a pothole-only, 12-endpoint system. Treat the code as the
source of truth and prefer updating those docs over trusting them.
