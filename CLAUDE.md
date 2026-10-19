# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"OcuLubak" — a road damage detection system for Philippine LGUs. A YOLOv8 model scores road
survey videos for the four CRDDC 2022 classes (D00 longitudinal, D10 transverse, D20 alligator,
D40 pothole — RDD2022's own codes; there is no D30), detections are geo-located from an uploaded
GPS track or from user-placed control points, and surfaced through a React web app with the thesis's two roles
(road maintenance personnel and system administrator, see "Roles"). The partner office is the Local Government Unit of
Mendez-Nuñez, Cavite (the seeded admin's `lgu_name`); never "DPWH Central Office". The web UI deliberately does not
show the LGU name anywhere (header, footer, login, metadata); keep it out of new UI copy too. Severity
scoring was dropped from the product: nothing computes, stores, returns or displays it.

Four independent parts: [backend/](backend/) (Flask API), [frontend/](frontend/) (React + Vite),
[ml/](ml/) (dataset prep + YOLO training, offline — the backend only loads a `.pt` from
`ml/models/`, see "Which model the backend loads"), and [mobile/](mobile/) (Expo capture app for iPhone and Android: records video + a
GPX on one phone and posts both to the unchanged `/api/videos/upload`; capture only, no on-device
inference). The team captures survey data on iPhones. Platform differences (screen lock, GPS rate,
`.mov` vs `.mp4`, upload transport) are tabled in [mobile/README.md](mobile/README.md) and all
platform branches live in `mobile/src/platform.js` / `mobile/src/api.js` — keep them there and keep
that table current. The mobile UI follows [frontend/design.md](frontend/design.md) as well:
`mobile/src/theme.js` mirrors the `:root` tokens of `frontend/src/index.css` and `mobile/src/icons.js`
reuses the paths of `frontend/src/icons.jsx`, so a visual change goes into both.

## Commands

Run everything from the repo root. The launcher scripts `cd` into the right subdirectory themselves.

```bash
# Easiest: double-click install_mac.command / install_windows.bat once. They install the packages,
# download the model weights with Git LFS, and create an "OcuLubak" app/shortcut that starts both
# servers hidden and opens the browser ("Stop OcuLubak" stops them). Scripts live in launcher/;
# logs and pids in the gitignored .oculubak/.

# One-time setup (manual)
python -m venv .venv && .venv\Scripts\activate   # Windows; source .venv/bin/activate elsewhere
pip install -r requirements.txt
cd frontend && npm install && cd ..
python backend/migrate.py                        # optional: create_app() also runs it on every boot

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

The backend binds `0.0.0.0:5000` so phones on the same LAN can reach it. `GET /api/server/info`
([backend/routes/server_info.py](backend/routes/server_info.py)) reports the address phones should use,
and the Overview page shows it in a "Connect a phone" panel (`PhoneConnect.jsx`), hidden until **Show**. The mobile app's server URL
is set on its login screen and persisted in SecureStore; `DEFAULT_SERVER_URL` in
[mobile/src/config.js](mobile/src/config.js) is only the first-run default.

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
`ml/models/best.pt`. The checked-in [ml/data.yaml](ml/data.yaml) is a four-class template
(`nc: 4`, index order = `TARGET_CLASSES` in `dataset_prep.py`); each prep script overwrites it with
real paths. Datasets and run artifacts are gitignored; `.pt` files are Git LFS (`git lfs pull`).

**Which model the backend loads** is the single `MODEL_PATH` line in
[backend/app.py](backend/app.py). It currently points at `ml/models/rdd2022_pretrained.pt`, an
external MIT-licensed 7-class YOLOv8n RDD2022 baseline used as an SE2 demo placeholder. It is
**not the team's model and its numbers must never be reported as thesis results** — Chapter 4
figures come from the team's own four-class fine-tune. Swapping that line back to `best.pt` restores
the team's model.

## Architecture

### Auth: signed tokens, one middleware

`POST /api/auth/login` returns `token` (HS256 JWT, `sub` = user id, expiry `JWT_EXPIRY_HOURS`,
default 12) plus `user`. [backend/auth_tokens.py](backend/auth_tokens.py) registers a
`before_request` hook: every `/api/*` request needs `Authorization: Bearer <jwt>` for an existing,
`active` user, or it gets a 401 with `code` = `token_missing` / `token_expired` / `token_invalid` /
`user_inactive` before the route runs. Exceptions are the endpoint names in `PUBLIC_ENDPOINTS`
(login, logout, anonymous report submission). The media endpoints in
`QUERY_TOKEN_ENDPOINTS` also accept `?token=`, because `<video>`/`<img>` cannot send headers.
There is no Flask session and no server-side logout; a token is valid until it expires.

The signing key is `SECRET_KEY` from the environment, else a random key generated into the
gitignored `backend/.secret_key` on first boot. Deleting that file logs everyone out.

Routes read the caller with `current_user_id()` / `current_user()` from `auth_tokens` (most route
files import it as `get_user_id`). A new route is protected by default; add its endpoint name to
`PUBLIC_ENDPOINTS` only if it must work logged out.

Survey scoping goes through one place: `visible_videos()` / `video_scope()` in `auth_tokens` (every
survey for an admin, the caller's own otherwise). `videos` (including the stream endpoints),
`detections` and `dashboard/stats` use it. `map` and `database` return every record to both roles, and
mark each with `can_open_video` / `can_open` so the UI only links to surveys the caller may open.

The web client keeps the token in `localStorage` (`token`); [api.js](frontend/src/api.js) attaches it,
appends it to media URLs, and on any 401 outside login clears it and fires `auth:expired`, which
`App.jsx` turns into the login screen with a notice.

### Roles

Two roles, matching the thesis (Chapter 3 §3.5, Fig. 3.5.1): `personnel` (Road maintenance personnel)
and `admin` (System administrator), defined in `models.ROLES`. The admin can do everything personnel
can, plus:

| Admin only | Server check | UI |
|---|---|---|
| Manage user accounts (create, change name/role, turn off/on, reset password) | `admin_required` on `/api/accounts` | Administration › Accounts |
| View the activity log | `admin_required` on `/api/activity` | Administration › Activity log |
| Manage detections: correct the kind of damage or road name, delete a record, accept/reject resident reports | `admin_required` on `PATCH`/`DELETE /api/database/detections/<id>` and report validate/reject; `PUT .../status` refuses `road_name`/`repair_status` from personnel | More menu per record on Damage records |
| See every survey | `visible_videos()` | Surveys list shows "By <name>" |

Both roles: upload and record (web and phone), their own surveys, the damage map, the damage records
list, inspection status, export. The server enforces all of this; `ROLE_ROUTE_ACCESS` in
[frontend/src/roles.js](frontend/src/roles.js) only decides what the web app shows, and unknown roles
fall back to `personnel`. There is no self-registration (`/api/auth/register` was removed). Accounts are
never deleted; `account_status = 'inactive'` blocks sign-in and fails the next request with
`user_inactive`. The last active admin cannot be demoted or turned off, nor can an admin change their
own role or status. `migrate.py` maps the older roles (`barangay`, `municipal`, `provincial`,
`public`, `inspector`) to `personnel` and old pending/rejected registrations to `inactive`.

**Activity log.** [backend/services/activity.py](backend/services/activity.py) `record()` writes one
`ActivityLog` row per action (sign-ins and refusals, survey upload/rename/delete/placement, status
changes, record corrections and deletions, exports, report review, account changes) after the
route's own commit; a logging failure never breaks the action. `ACTIONS` there is the list of codes
and labels, and the API sends it to the web app. A new action goes there first.

### Video processing pipeline

[backend/routes/videos.py](backend/routes/videos.py) saves the upload, pulls metadata with OpenCV,
then spawns a bare `threading.Thread` running
[backend/services/video_processor.py](backend/services/video_processor.py). No queue, no worker
process — processing dies with the server and does not survive a restart; `create_app()` marks any
video still `uploaded`/`processing` as `failed` on boot so nothing spins forever. Uploads longer than
`MAX_VIDEO_DURATION_S` (600 s) are rejected with 400 before a thread is spawned. A failed analysis
stores a user-facing reason in `Video.error_message` (shown on the web and the phone), and
`POST /api/videos/<id>/reprocess` reruns a failed or finished survey from the files already on the
server ("Analyse again"; it replaces the damage records, so the clients confirm first for a finished
one). The phone's survey screen also has "Upload again as a new survey", for testing changes.
`model_file_problem()` in `video_processor.py` catches a missing model or a Git LFS placeholder
(a clone without `git lfs pull`): the backend warns at startup and the analysis fails with that reason. There is currently
**no size cap**: `MAX_CONTENT_LENGTH = None` in `app.py` and `MAX_VIDEO_BYTES = null` in
`mobile/src/config.js` (iPhone recordings outgrew 500 MB). The mobile limits in `config.js` mirror the
backend ones with a margin (`MAX_RECORD_S = 590`), so change both sides together. Progress is written
to `Video.processing_progress` every 30 frames and the frontend polls for it.
`GET /api/videos/export` returns per-video frames / sampled frames / processing seconds — the
throughput data for the thesis evaluation chapter.

Inside `_run_detection_pipeline`:

- Only detections with their box centre below `ROAD_REGION_TOP` (0.5: the lower half of the frame)
  are kept, so buildings and trees above the road are not reported. The model still sees the whole
  frame. The phone's camera screen has a level guide ([mobile/src/level.js](mobile/src/level.js))
  so the horizon lands on that line; the annotated video draws it.
- Frames are read through `open_upright()`: a phone recording held sideways or upside down carries a
  rotation flag, not rotated pixels, and OpenCV does not apply it by default. Without this the model
  sees upside-down frames and the annotated video plays upside down. The upload route uses the same
  helper, so `resolution` is the displayed size.
- Inference runs on every `fps/INFERENCE_FPS`-th frame at `CONF_THRESHOLD` / `IOU_THRESHOLD` — module
  constants at the top of `video_processor.py` that the thesis cites; change them there only. Between
  inference frames the last boxes are re-drawn for `fps*0.5` frames so the annotated video does not flicker.
- Each damage is recorded once: [services/damage_tracker.py](backend/services/damage_tracker.py) joins
  sightings across analysed frames into tracks (after dropping same-frame boxes lying mostly inside a
  more confident one, `TRACK_NESTED`; then overlap `TRACK_MIN_IOU`, or the centre landing in
  the area below the last box the damage can move to; a track ends after `TRACK_MAX_GAP_S` unseen),
  and each track becomes one row from its best (highest-confidence) sighting: that frame's box,
  time, position and snapshot. Run `python services/damage_tracker.py` for its self-checks. It
  replaced a `(100px grid cell, 2 s window)` key that stored the same pothole again as it moved
  down the picture.
- `_classify_damage` maps model class names to RDD2022 codes (D00/D10/D20/D40) by substring, then
  (for models with ≤5 classes) falls back to class index in the `ml/dataset_prep.py` order; a
  single-class model maps everything to `D40`. For models with more than 5 classes,
  `_is_pothole_class` first drops any class whose name is not one of the four codes (or
  `pothole`/`hole`). Generic names like `crack` are deliberately excluded so they are not filed as D40.
  The team's own `best.pt` is **still single-class** (`nc: 1`, name `pothole`). Retraining on four
  classes is the open critical-path task.
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
exists must be listed in [backend/migrate.py](backend/migrate.py). `create_app()` calls its
`migrate()` (idempotent) before `create_all()` on every boot, so ORM queries never hit a stale schema.
The same script remaps rows written under the
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
3. New page in `frontend/src/pages/` (start it with `<PageHeader>`), plus a `<Route>` in `App.jsx`,
   an entry in `NAV_ITEMS` ([Header.jsx](frontend/src/components/Header.jsx), with an icon from
   `icons.jsx`), and the path added to `ROLE_ROUTE_ACCESS` in `roles.js`.
4. Decide who may call it. Admin only: `@admin_required`. Survey data: query through
   `visible_videos()`. Log user actions with `services.activity.record()`.

### Frontend conventions

The Vite dev server talks to `http://localhost:5000/api`, hard-coded in `api.js` — there is no proxy
and no env var, so changing the backend port means editing that constant. All styling lives in one
global [frontend/src/index.css](frontend/src/index.css) whose `:root` tokens (`--color-*`, `--text-*`,
`--space-*`, `--radius-*`, `--elevation-1`) are the only source of values, built against
[frontend/design.md](frontend/design.md), the authority on every visual decision. In brief: one navy
header bar, white page, the logo green `#046B3E` as the single primary/link colour, at most one filled
green button per view, grouping by space and panels rather than lines, Public Sans (400/600/700) with
tabular figures (`.num`), status always as icon plus words, monospace for code only. There are no CSS
modules or component-scoped styles, and no UI or icon library: icons are hand-written SVG in
[icons.jsx](frontend/src/icons.jsx). Pages are plain function components using `useState`/`useEffect`
polling, with no state library and no data-fetching library.

Shared pieces in `frontend/src/components/`:
- `Header` (navy bar, role-filtered nav, account menu, phone menu below 64rem) and `Footer`
  (`SUPPORT_CONTACT` renders nothing while empty).
- `PageHeader` (back link, title, meta line, actions, tabs slot) and `Notice` (info/success/error).
- `StatusLabel` (`SurveyStatus`, `LocationSource`, `ProgressBar`), `EmptyState`, `SkeletonRows` and
  `ErrorSummary` (GOV.UK pattern).
- `Disclosure`: menus as a button with `aria-expanded` and a panel, not ARIA `role="menu"`.
- `ConfirmDialog` (native `<dialog>`) and `RenameVideo` (a rename form the parent shows).

[frontend/src/labels.js](frontend/src/labels.js) holds the plain-language names for damage codes and
statuses, the upload limits, and the survey predicates `isRunning` / `hasLocation` /
`canPlaceByHand`. Show a class name with its code beside it (`.code`), never a code alone.
`useMediaQuery(WIDE)` is used only where phone and desktop need different markup (map filters and
legend, records table vs cards).

Survey detail and "Place on the map" are two tabs of one page,
[SurveyPage.jsx](frontend/src/pages/SurveyPage.jsx) (shared header and polling), with bodies in
`SurveyDamageTab.jsx` and `SurveyPlaceTab.jsx`. Both URLs (`/videos/:id`, `/videos/:id/georeference`)
stay; the second tab only shows for surveys without GPS that did not fail.

The map page ([DamageMapPage.jsx](frontend/src/pages/DamageMapPage.jsx)) is deliberately plain:
OpenStreetMap tiles, one solid navy route per survey with labelled Start/End markers, and one
`CircleMarker` dot per detection coloured by damage class. A GPS-measured dot is solid with a white
halo; a hand-placed one has a dashed stroke over a 35% fill. The four class colours (`DAMAGE_CLASSES` at
the top of that file) encode data and appear only on the map (dots, legend, popup swatch). No heatmap,
no clustering: `leaflet.markercluster` is a dependency but must stay unused. Every `<MapContainer>`
takes `OSM_TILES` / `OSM_ATTRIBUTION` and a `<MapResizeFix />` child
([components/MapResizeFix.jsx](frontend/src/components/MapResizeFix.jsx)), which re-measures the map
when its box changes; without it the map can stay grey or load only some tiles.

## Documentation in the repo

[README.md](README.md), [backend/README.md](backend/README.md), and
[backend/API_REFERENCE.md](backend/API_REFERENCE.md) predate the GPS, map, public-report, database,
and accounts features — they describe a pothole-only, 12-endpoint system. Treat the code as the
source of truth and prefer updating those docs over trusting them.

[CHAPTER3_SYSTEM_OVERVIEW.md](CHAPTER3_SYSTEM_OVERVIEW.md) (draft Chapter 3 prose) and
[CHAPTER3_REVISION_OVERVIEW.md](CHAPTER3_REVISION_OVERVIEW.md) (what has to change in Chapter 3,
with `file:line` pointers) are written from the code. The code can drift from them, so update them
alongside behaviour changes they describe. [figures/](figures/) holds the Chapter 3 diagrams. The
Mermaid `.mmd` file is the source and the `.png`/`.svg` files are renders, so edit the `.mmd`
file and re-render it.
