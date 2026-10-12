# Chapter 3 Revision Overview (reconnaissance)

Inventory of what has to change in Chapter 3. Nothing here is Chapter 3 prose and nothing in
the thesis has been edited.

**Inputs used**

- Codebase at the current working tree (branch `gian-branch`, uncommitted changes included).
- Revised Chapters 1–2: `THESIS CHAPTERS 1-3 REVISED 1-2.pdf` (May 2026).
- Existing Chapter 3: the unrevised Chapter 3 in the same PDF, used as the draft being revised.

**Conventions**

- `p. N` is the page number printed in the PDF footer.
- `file:line` points into this repository.
- "Not measured" means the value does not exist yet. No number in this report was estimated to
  fill a gap.

---

## 0. Corrections to the brief

The brief says to flag anything in it that the code contradicts. These need a decision before
revision starts.

| Brief says | What is actually true | Evidence |
|---|---|---|
| Roles: two only (Road Maintenance Personnel, System Administrator). | The code has four roles in the web app (`barangay`, `municipal`, `provincial`, `admin`) and five in the backend (adds `public`). Self-registration is still live for `public`, `barangay`, `municipal`, `inspector`. The two-role model exists only in the thesis text. | `frontend/src/App.jsx:16-21`; `backend/models.py:11`; `backend/routes/auth.py:16`; `backend/auth_tokens.py:28` |
| YOLOv8m inference. | The backend currently loads an **external YOLOv8n demo model** (`rdd2022_pretrained.pt`: 7 classes, 3.0 M parameters, imgsz 640), not the project's weights. The code comment says it must never be reported as a thesis result. The project's own `best.pt` is YOLOv8m (25.86 M parameters) but has **one class** (`pothole`) and was trained at imgsz 1024. | `backend/app.py:28-34`; weights inspected with Ultralytics 8.4.155 |
| Severity scoring removed entirely. | Nothing computes, returns or displays it. The `Detection.severity` / `severity_score` columns remain (never written) and `services/severity_service.py` is kept with no callers. Chapter 3 can say severity is not part of the system; it should not say the code contains no trace of it. | `backend/models.py:171-174`; `backend/services/video_processor.py:92-93` |
| Mobile app "verified on iOS only". | It has been installed and run on an iPhone 16 during development, but every item in the repo's device-test checklist is unchecked. A save-after-recording bug was fixed on 2026-10-08 and the fix has not yet been confirmed on the phone. No end-to-end record → upload → process → map run has been confirmed. "Verified" is stronger than the evidence. | `mobile/README.md:122-136` |
| Mobile app "records video and GPS synchronously". | It records them concurrently on **two different clocks**: the video start is taken from the device clock, and GPS fixes carry their own timestamps. They are reconciled afterwards by `time_offset` and a median clock-skew term. Chapter 3 should say "concurrently" and describe the alignment. | `mobile/src/gpx.js:63-67` |
| Known mismatch: "Split ratio stated as 80/15/5". | 80/15/5 **is** what the code uses for RDD2022 in all three preparation scripts, so it does not contradict the code. The real gaps are elsewhere: a code comment says the local set uses 70/15/15, nothing in the code builds a local split, and Objective 1 needs separate foreign and local test subsets. | `ml/dataset_prep.py:36-37`; `ml/download_rdd2022.py:28-29`; `ml/convert_rdd2022.py:29` |
| "Algorithm 3.1". | The document labels it "Algorithm 1" (p. 43). | — |
| "One figure with no caption at all." | Every figure in this PDF has a caption. The unnumbered items are three tables (2.3.1 synthesis table, the weighted-mean interpretation scale on p. 64, the software tools table on p. 65). There is also a state diagram in `Documents/diagrams/3.5_state_diagram.png` that the chapter does not use. One of these may be what the brief means (see Q15). | — |

---

## Section 1 — Code-extracted facts

### 1.1 Detection pipeline (`backend/services/video_processor.py`)

**Frame sampling.** Not every frame is inferred.

- `INFERENCE_FPS = 5` (`:12`); `process_every_n = max(1, int(fps / INFERENCE_FPS))` (`:261`).
- A frame is inferred when `frame_number % process_every_n == 0` (`:287`).
- At 30 fps that is every 6th frame (5 inferences per second of video). At 24 fps it is every 4th
  (6 per second). Because of the `int()` truncation, the effective rate depends on the source fps.
- Every frame is still decoded, annotated and written to the output video (`:371-379`).
- Between inferences, the last boxes are redrawn for `int(fps * 0.5)` frames so the output does
  not flicker (`:267`, `:283-285`).

**Deduplication.** This decides what makes two detections "the same damage".

- Key = `((int(x1/100), int(y1/100)), frame_number // int(fps*2))` (`:316-317`). In words: the
  top-left corner of the box in a 100-pixel grid cell, within the same fixed 2-second window of
  video.
- The first detection with a given key becomes a database row. Later ones with the same key are
  drawn on the video but not stored (`:319-320`).
- The key ignores the damage class. Two different classes whose boxes start in the same cell
  within the same window collapse into one row.
- The windows are fixed buckets, not sliding. The same pothole seen at 1.9 s and 2.1 s falls into
  two windows and produces two rows.
- Nothing links detections across windows. The same pothole visible for 6 s produces about three
  rows.

**Thresholds.**

- `CONF_THRESHOLD = 0.15` (`:13`) and `IOU_THRESHOLD = 0.45` (`:14`), passed to Ultralytics per
  call (`:290`).
- NMS is Ultralytics' per-frame, class-aware NMS (`agnostic_nms` default `False`; `max_det`
  default 300).

**Inference image size.** No `imgsz` is passed at `:290`. Ultralytics carries the training
`imgsz` into inference for a loaded checkpoint, so `best.pt` infers at 1024 and the demo model at
640.

**Model loading.**

- `MODEL_PATH` is the demo model (`backend/app.py:34`).
- If the file is missing, the code falls back to COCO `yolov8n.pt` (`:115-127`).

**Class mapping.** `_classify_damage` (`:174-199`) works in three steps:

1. Substring match on the class name against `DAMAGE_CLASS_MAP` (`:19-30`).
2. For models with 5 or fewer classes, fall back to class index 0..3 → D00/D10/D20/D40. A
   single-class model maps everything to D40 (`:188-196`).
3. Otherwise D40 with `is_damage = False`.

With the 7-class demo model, the `block`, `crack` and `edge` classes are dropped (`:440-450`).

**Timestamp.** `timestamp = frame_number / fps` (`:323`). `frame_number` is incremented before
use (`:276`), so the first frame is 1/fps, not 0. The error is one frame (about 33 ms at 30 fps).

**Output video.**

1. OpenCV writes MJPG AVI, with XVID AVI as a fallback (`:235-252`).
2. If `ffmpeg` is on PATH, the AVI is re-encoded to H.264 MP4: `libx264 -preset ultrafast -crf 18
   -pix_fmt yuv420p -movflags +faststart`, with a 600 s timeout (`:493-534`).
3. Without ffmpeg, the AVI is kept (`:406-418`).

`processed_filename` records whichever file survived (`:95-98`).

**Snapshots.** One JPEG per stored detection, with its box drawn (`:342-348`).

**Upload checks and processing.**

- Formats accepted: mp4, avi, mov, mkv, webm (`backend/routes/videos.py:17`).
- Duration cap: 600 s, enforced after the file is saved (`videos.py:65-72`; `app.py:27`).
- Upload size cap: **none** (`MAX_CONTENT_LENGTH = None`, `app.py:24-26`, changed 2026-10-08;
  it was 500 MB).
- Processing runs in a daemon `threading.Thread` started straight from the upload request
  (`videos.py:117-124`).
- On restart, any video still `uploaded`/`processing` is marked `failed` (`app.py:82-89`).
- Progress is written every 30 frames (`:278-281`).

**Throughput data.** `GET /api/videos/export` returns per video: frames, sampled frames,
`INFERENCE_FPS` and wall-clock `processing_seconds` (`videos.py:132-185`). This is the
measurement source for any throughput figure.

### 1.2 GPS synchronisation (`backend/services/gps_service.py`)

**Parsing.**

- GPX: track points, falling back to waypoints (`:13-53`).
- CSV: delimiter is sniffed; column names are matched case-insensitively (`:56-125`). A CSV with
  no time column gets synthetic 1-second timestamps (`:120-123`).
- All timestamps are normalised to **seconds from the first point**, after sorting (`:155-177`).

**`interpolate_gps`** (`:195-256`):

- `gps_time = video_timestamp + time_offset` (`:214`).
- Linear interpolation between the two bracketing points (`:231-254`), rounded to 7 decimal
  places.
- **It clamps.** If `gps_time` is at or before the first point, it returns the first point
  (`:217-222`). If it is at or after the last point, it returns the last point (`:224-229`).
  Detections outside the track therefore get a coordinate, and it is wrong.

**Validation.**

- A track shorter than 1 s is rejected, and the video is then processed as if it had no GPS
  (`:275-281`; `video_processor.py:149-151`).
- Coverage below 100 % is only reported in a message, not rejected (`:283-293`).
- Every parsed point is stored as a `GpsTrackPoint` (`video_processor.py:153-165`).

**`time_offset` sign convention.**

- Positive means the video started *after* the GPS track started:
  `gps_time = video_time + time_offset`.
- It comes from the `time_offset` form field, default 0 (`videos.py:91`).
- The mobile app computes it as
  `((videoStart_device − clockSkew) − firstFix_time) / 1000` (`mobile/src/gpx.js:63-67`), which
  follows the same convention.

### 1.3 Georeferencing (`backend/services/georeference_service.py`)

**Purpose.** A fallback for videos uploaded without a GPS track. The user places
(video time → map coordinate) control points.

**Validation** (`:35-78`):

- At least 2 points.
- Numeric values.
- `video_time_s` strictly increasing, between 0 and the video duration.
- Latitude 4.5–21.5 and longitude 116.0–127.0, a Philippine bounding box (`:15-16`).

**Interpolation** (`:81-115`):

- Piecewise-linear between the two bracketing control points.
- **It never clamps.** A time outside [first, last] returns `None`, so the detection stays
  unpositioned.

**Applying.** `apply_control_points_to_detections` (`:118-154`) repositions every detection of
the video and resets the ones outside the control-point range to `none`.

**When it can be used.**

- `POST /api/videos/<id>/control-points` is refused if the video has a GPS file, with a 409
  (`videos.py:383-384`).
- It is also refused while the video is still processing (`videos.py:385-386`).

### 1.4 How `position_source` is assigned

**Video level.**

- Set at upload: `'gps_file'` if a GPS file was attached, otherwise `'none'` (`videos.py:108`).
- Changed to `'georeferenced'` only when control points are saved (`georeference_service.py:148`).

**Detection level** (`video_processor.py:326-340`):

- `'gps_file'` when `gps_points` loaded and `interpolate_gps` returned a value. Because
  `interpolate_gps` clamps, this is effectively always once a track loads.
- Otherwise `'georeferenced'` when control points were present at processing time.
- Otherwise `'none'`.

**Inconsistencies to know about.**

1. A video whose GPS file fails parsing or validation keeps `position_source = 'gps_file'` at
   video level while all its detections are `'none'`. Nothing resets the video row.
2. The control-point branch inside the pipeline (`video_processor.py:72-76`, `:335-340`) cannot
   be reached. Control points can only be saved after processing ends (409 otherwise), and there
   is no reprocess route. In practice every `'georeferenced'` value comes from
   `apply_control_points_to_detections`.

**Map routes.** `GET /api/map/gps-tracks` returns one route per survey: the full stored track for
GPS-file surveys, or straight segments between control points (`source: control_points`) for
hand-placed ones (`backend/routes/damage_map.py:94-138`).

### 1.5 Data model (`backend/models.py`)

| Model | Fields actually stored |
|---|---|
| `User` (`:35-77`) | id, username, password_hash, full_name, lgu_name, role (default `'inspector'`), agency, sector_level, email, created_at, account_status, id_photo, rejection_reason |
| `Video` (`:80-143`) | id, filename, original_filename, display_name, file_size, duration, fps, resolution, status, processing_progress, upload_date, processed_date, processed_filename, total_detections, user_id, gps_filename, gps_original_filename, time_offset, road_name, position_source |
| `Detection` (`:146-217`) | id, video_id, frame_number, timestamp, confidence, bbox_x1/y1/x2/y2, frame_snapshot, created_at, damage_type, damage_label, latitude, longitude, position_source, severity *(legacy, unused)*, severity_score *(legacy, unused)*, road_name, inspection_status (`pending_validation`/`inspected`/`scheduled`/`ongoing_repair`/`resolved`, `:23-29`), repair_status, source_type (`ai_detection`/`public_report`) |
| `GpsTrackPoint` (`:220-239`) | id, video_id, timestamp (s from track start), latitude, longitude, elevation |
| `RouteControlPoint` (`:242-263`) | id, video_id, seq, video_time_s, latitude, longitude, created_at |
| `PublicReport` (`:266-316`) | id, reporter_name, reporter_contact, image_filename, description, latitude, longitude, manual_location, damage_type, damage_label, status, validated_by, rejection_reason, created_at, updated_at, submitted_by |

`DAMAGE_TYPES` = D00 Longitudinal, D10 Transverse, D20 Alligator, D40 Pothole (`:15-20`). There
is no D30.

### 1.6 Training configuration (`ml/`)

There are **two training scripts with different settings**. The existing `best.pt` was produced
by the second one (its stored training args show imgsz 1024).

| Setting | `train_model.py` (says it matches the thesis) | `train_local.py` (produced current `best.pt`) |
|---|---|---|
| Base weights | `yolov8m.pt`, COCO-pretrained (`:72-75`) | `yolov8m.pt` (`:16`) |
| Epochs / early stopping | 100, patience 20 (`:28-31`) | 150, patience 30 (`:24`, `:62`) |
| Batch | 16 (`:29`) | 4 (`:25`) |
| imgsz | 640 (`:30`) | 1024 (`:26`) |
| Optimiser | AdamW, lr0 0.001, lrf 0.01, wd 0.0005, warmup 3 (`:92-98`) | auto, lr0 0.01, warmup 5 (`:33-38`) |
| Augmentation | hsv 0.015/0.7/0.4, degrees 10, translate 0.1, scale 0.5, shear 2.0, perspective 0.0001, flipud 0.5, fliplr 0.5, mosaic 1.0, mixup 0.15 (`:101-112`) | hsv same, degrees 15, translate 0.2, scale 0.5, flipud/fliplr 0.5, mosaic 1.0, mixup 0.15, close_mosaic 20 (`:43-56`) |
| Acceptance bar | mAP@50 ≥ 0.50, "on the local test subset" (`:32`, `:211`) | none |

**Dataset preparation.**

- Four classes only: `TARGET_CLASSES = {D00:0, D10:1, D20:2, D40:3}` (`dataset_prep.py:33`).
- Split 80/15/5 with seed 42 (`dataset_prep.py:36-37`; `download_rdd2022.py:18,28-29`;
  `convert_rdd2022.py:29-30`).
- Per-class cap: default 2,500 images in `download_rdd2022.py` (`:26`, env `RDD_MAX_PER_CLASS`),
  optional in `dataset_prep.py` (`--max-per-class`). An image counts toward every class it
  contains (`dataset_prep.py:113-140`).
- `download_rdd2022.py` reads only each country's `train` folder (`:161`).

**Local (Philippine) data.** No code ingests, splits or labels it. The only trace is the comment
"local set uses 70/15/15" (`dataset_prep.py:36`).

**Evaluation.**

- `evaluate_model.py` evaluates `split='val'`, not `test`, with batch 4 (`:32`).
- Nothing evaluates foreign and local subsets separately.
- `train_model.py` prints per-class AP@50 and computes F1 from Ultralytics' mean P/R
  (`:149-177`).

**Losses.** Ultralytics' v8 detection loss uses `BCEWithLogitsLoss` for classification (not
cross-entropy), plus CIoU and DFL (`ultralytics/utils/loss.py`, `v8DetectionLoss`).

**Shipped weights.**

- `ml/models/best.pt`: nc = 1 `{0: 'pothole'}`, 25,856,899 parameters, trained imgsz 1024.
- `ml/models/rdd2022_pretrained.pt`: nc = 7, 3,012,213 parameters, imgsz 640. This is the
  external demo model.

### 1.7 Mobile capture app (`mobile/`)

**Recording limits.**

- Duration: 590 s (`src/config.js:6`).
- Size cap: off (`MAX_VIDEO_BYTES = null`, `:12`; changed 2026-10-08).
- Will not start below 2 GB free storage (`:23`).
- 1080p (`:16`), 5 Mbit/s **requested** (`:17`; passed at `src/screens/CaptureScreen.js:283-284`).
- iOS: H.264 is forced with `codec: 'avc1'` (`src/platform.js:28`). The container is `.mov` on
  iOS and `.mp4` on Android (`platform.js:32-36`).
- Muted (`CaptureScreen.js:282`).
- The app does not set a frame rate; the camera default applies (not measured).
- *Observed during development:* iPhone 16 recordings exceeded 500 MB in under 10 minutes. 5
  Mbit/s would give about 37 MB/min, so the requested bitrate may not be applied. Not measured.

**Start gate.** Recording cannot start until a GPS fix is under 5 s old and within ±20 m
(`config.js:27-28`; `CaptureScreen.js:112,269`).

**After stop.**

- The movie's `moov` index is checked; an incomplete file is marked failed, not uploaded
  (`src/capture.js:71`).
- Stale fixes are dropped (`gpx.js:41`).
- Gaps over 3 s are flagged (`gpx.js:71`).
- Per-session metadata is written into the GPX `<bk:capture>` extension (`gpx.js:107`): platform,
  permission, offset, skew, achieved Hz, error count, stale fixes, container.

**GPS logging.**

- Background task with `BestForNavigation`, `timeInterval: 1000`, `distanceInterval: 0`,
  `AutomotiveNavigation`, `pausesUpdatesAutomatically: false` (`src/locationTask.js:70-74`).
- **On iOS the sampling rate cannot be set.** iOS ignores `timeInterval`; the rate is whatever
  Core Location delivers. The app records `achievedHz` per session (`mobile/README.md:106`). That
  statement is based on reading the source, not yet observed on a device.
- Each fix is appended to `points.jsonl` as it arrives (`locationTask.js:59`).

**`time_offset`.**

- `skew` = median over fixes of (device receipt time − fix timestamp).
- `time_offset = ((videoStart_device − skew) − firstFix_time) / 1000` (`gpx.js:63-67`).
- Sent as the `time_offset` form field with the GPX on the unchanged `POST /api/videos/upload`.

**Upload queue** (`src/uploadQueue.js`):

- One upload at a time, oldest first (`:76-78`).
- **Wi-Fi only by default** (`:13`, `:40-56`).
- Paused while recording (`:64`).
- Backoff 15 s × 2^(n−1) (`:123`), 5 automatic attempts (`:118`), then manual retry.
- 401: stays queued until login (`:111`).
- 400/413: not retried (`src/api.js:43-45`).
- iOS streams the multipart body from a temporary file (`api.js`, `mobile/README.md`).

**Files on the phone.** Recordings stay on the phone after upload until deleted. As of
2026-10-08, the user can also copy the video to Photos or share the video/GPX (`src/media.js`).

### 1.8 Authentication (`backend/auth_tokens.py`, `backend/routes/auth.py`)

**Issuing.**

- HS256 JWT with `sub` = user id, `iat`, `exp` (`auth_tokens.py:60-67`).
- Expiry `JWT_EXPIRY_HOURS`, default 12 (`app.py:17`).
- Key from `SECRET_KEY`, otherwise a random key generated into `backend/.secret_key`
  (`auth_tokens.py:40-57`).

**Verifying.**

- A `before_request` hook runs on every `/api/*` path except OPTIONS (`app.py:48`;
  `auth_tokens.py:83-108`).
- Requires `sub`, `exp` and `iat`.
- Rejects with 401 and one of `token_missing` / `token_expired` / `token_invalid` /
  `user_inactive`.

**Exempt endpoints** (`auth_tokens.py:25-30`): `auth.login`, `auth.logout`, `auth.register`
(still live), `public_reports.submit_report`.

**Token in the query string** (`?token=`). Accepted only on `videos.stream_original_video`,
`videos.stream_processed_video`, `videos.get_snapshot` and `public_reports.get_report_image`
(`auth_tokens.py:32-37`, `:74-80`), because `<video>`/`<img>` cannot send headers.

**Logout.** No server-side logout. A token stays valid until it expires (`routes/auth.py:162-165`).

**Server-side role checks.** Only `_require_admin()` in `routes/accounts.py:11`. Everything else
role-related is client-side (`App.jsx:16-31`).

**Data scoping** (relevant to the ethics section).

- Filtered by owner: `videos` list, `detections/<video_id>`, `dashboard/stats`, control points,
  `videos/export`.
- **Not filtered**, returned to any logged-in user: map detections and tracks
  (`damage_map.py:36-60`), database list, status update and export (`database.py:14-153`), media
  streams and snapshots (`videos.py:288-330`), report reads (`public_reports.py:97-105`).

### 1.9 Other features that exist but Chapter 1 does not mention

- **Inspection workflow.** `Detection.inspection_status`, changed via
  `PUT /api/database/detections/<id>/status` (`database.py:80`).
- **Public (citizen) reports.** Submission is anonymous and validated reports are promoted into
  `Detection` rows (`routes/public_reports.py`). The backend supports this, but no frontend page
  uses it.
- **Survey management.** Rename and delete surveys (`videos.py:220-286`).
- **Raw-upload retention.** `backend/purge_uploads.py`, 30-day default, dry-run unless `--apply`
  (`:20`).
- **Export.** CSV and JSON only (`database.py:115-152`). **There is no PDF export anywhere.**

---

## Section 2 — Where the current Chapter 3 contradicts the code

Grouped by section, in page order. "Code" gives the actual behaviour with its citation.

### 3.1 Development methodology (pp. 28–35)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.1 | Fig. 3.1 "shown separately in the figure as directions for future iterations" (p. 29) | The figure is a generic stock Agile wheel. It has no phases and no future-iterations element. |
| 2.2 | Phase 1: "Collecting and preprocessing the RDD2022 dataset and locally collected road images" (p. 30); Phase 2: "Retraining the YOLOv8 model using expanded datasets and local road images … This iteration significantly improved detection relevance" (p. 31) | No local data exists, and no four-class model has been trained (`best.pt` nc = 1). These are written as completed results with no evidence behind them. |
| 2.3 | Phase 5: "Detection accuracy evaluation", "Final system validation", "transitioned … into a validated platform" (p. 33) | No evaluation has been run. `evaluate_model.py` targets `val`, not test (`:32`). |
| 2.4 | 3.1.6 future work: "Live GPS synchronization", "Multi-user collaboration and monitoring features" (p. 34) | Concurrent GPS capture now exists in the mobile app (not live). The system is already multi-user. Both items need rewording. |

### 3.2.1 Conceptual framework figure and text (pp. 34–38)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.5 | Fig. 3.2.1 classes "D10 Longitudinal Crack, D20 Transverse Crack, D30 Alligator Crack, D40 Pothole" (p. 35) | D00 / D10 / D20 / D40; no D30 (`models.py:15-20`). The text on p. 36 has the right codes, so figure and text disagree. |
| 2.6 | Fig. 3.2.1 "RDD2022 Dataset (26,620+ road images)"; text "filtered subset of 26,620 images" (p. 36) | Not produced by any script. `download_rdd2022.py` caps at 2,500 per class by default (`:26`). The final count is not measured (Section 5). |
| 2.7 | "resized to 640×640 pixels (the required input dimensions for YOLOv8m)" (p. 36); figure "Image Resizing (640×640)" | imgsz is a setting, not a requirement. The existing `best.pt` was trained and runs inference at 1024 (`train_local.py:26`; checkpoint args). |
| 2.8 | Augmentation "rotation, horizontal flipping, mosaic augmentation, and scaling" (p. 36) | Also HSV jitter, translate, shear, perspective, vertical flip and mixup (`train_model.py:101-112`). |
| 2.9 | "100 epochs with a batch size of 16" (p. 37) | Matches `train_model.py` but not `train_local.py` (150 / 4 / 1024), which produced the current weights. See Q2. |
| 2.10 | "Cross-Entropy Loss for damage class classification" (p. 37; figure; YOLOv8 figure) | Ultralytics v8 uses binary cross-entropy with logits (`v8DetectionLoss`). |
| 2.11 | "the confidence threshold is calibrated (default 0.3) … NMS IoU threshold is set to 0.5" (p. 37); figure "Confidence Threshold: 0.3 / NMS IoU Threshold: 0.5"; "Post-Processing: Confidence Thresholding (≥0.3) + NMS (IoU=0.5)" | `CONF_THRESHOLD = 0.15`, `IOU_THRESHOLD = 0.45` (`video_processor.py:13-14`). No calibration procedure exists. |
| 2.12 | "a road survey video file (MP4, AVI, or MOV format)" (p. 37); figure "(MP4/AVI/MOV)" | Also MKV and WebM (`videos.py:17`). |
| 2.13 | "OpenCV's VideoCapture extracts individual frames … Each frame is then passed through the YOLOv8m inference engine" (p. 38); figure "YOLOv8m Inference (per frame)" | Every `int(fps/5)`-th frame (`video_processor.py:261,287`). |
| 2.14 | "Non-Maximum Suppression (IoU = 0.5) to eliminate duplicate detections for the same damage instance" (p. 38) | NMS works within one frame. Duplicates of the same damage across frames are removed by the separate grid-cell + 2-second-window key (`:316-320`), which the chapter never mentions. |
| 2.15 | "statistical reports with data export capabilities in JSON, CSV, and PDF formats" (p. 38); figure "(JSON/CSV/PDF)" | CSV and JSON only (`database.py:115-152`). No PDF anywhere. |
| 2.16 | The "System Input" paragraph requires both a video and a GPS file (p. 37) | The GPS file is optional (`videos.py:74-88`). Without it, detections stay unpositioned until control points are placed. |

### 3.2.2 System architecture (pp. 39–41)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.17 | Fig. 3.2.2 client modules "Video Upload Interface, Results Dashboard, Detection Timeline, Export Module" | Actual pages: Login, Dashboard, Upload, Video list, Detection viewer, Georeference, Damage map, Database with export (`frontend/src/pages/`). There is no mobile client in the figure. |
| 2.18 | "Model Weights … yolov8m.pt"; "maintains the YOLOv8m pre-trained model file (yolov8m.pt) for inference" (p. 41) | Inference must use fine-tuned weights (`ml/models/best.pt`). `yolov8m.pt` is the COCO base checkpoint used only to start training. The code currently loads the demo model (`app.py:34`). |
| 2.19 | Application tier shows only the Video Processing Service | The GPS synchronisation service and the control-point georeferencing service are missing, and so is ffmpeg (an external dependency, `video_processor.py:493-534`). |
| 2.20 | "Three-Tier System Architecture" | With the mobile capture app there are now two clients. See Section 4 for the tier count. |

### 3.3.1 YOLOv8m algorithm and Algorithm 1 (pp. 41–44)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.21 | Algorithm 1 line 3–4: `F ← EXTRACT_FRAMES(V) // native frame rate`, `FOR EACH frame f IN F` | Sampled at `int(fps/5)` (`video_processor.py:261,287`). |
| 2.22 | Line 18: `// D10, D20, D30, D40` | D00 / D10 / D20 / D40. |
| 2.23 | Line 19: `conf ← OBJECTNESS(p) × IOU_PRED(p)` | YOLOv8's head is anchor-free and has **no objectness branch**. Confidence is the class score. This also affects Formula (6). |
| 2.24 | Inputs `Tc (default 0.3)`, `Ti (default 0.5)` | 0.15 / 0.45. |
| 2.25 | Line 38: `INTERPOLATE_GPS(G, tf)` | Leaves out `t_offset` (`gps_service.py:214`), even though Formula (19) includes it. It also leaves out clamping (`:217-229`), the no-GPS / control-point fallback, and the deduplication step (`:316-320`). |
| 2.26 | Input `M - trained YOLOv8m model (yolov8m.pt)` | Fine-tuned weights file (`best.pt`); see 2.18. |
| 2.27 | YOLOv8 architecture figure (p. 42): head labels "D10 Longitudinal / D20 Transverse / D30 Alligator / D40 Pothole" | Wrong codes. The figure also has typos ("Head Head", "Detec-Head") and repeats the INPUT/BACKBONE/NECK/HEAD labels at the bottom. |

### 3.3.2 Formulas (pp. 44–52)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.28 | Formula (1): "b = number of batches (16)"; "number of batches b per epoch (set to 16)" (p. 45) | 16 is the batch **size** (`train_model.py:29`), so in this notation it is *i*. *b* (batches per epoch) = ⌈N/16⌉ and depends on the dataset size N, which is not measured. |
| 2.29 | Formula (1): "approximately 25.9 million model parameters" | `best.pt` has 25,856,899, consistent. A 4-class head will differ slightly, so take the figure from the final weights. |
| 2.30 | Formula (2): "409,600 total pixels across 3 RGB channels" (p. 46) | 640×640 = 409,600 pixels per channel (1,228,800 values across 3). At imgsz 1024 it is 1,048,576 pixels. |
| 2.31 | Formula (3): "typically fewer than 100 detections per frame after confidence filtering" (p. 46) | Not measured. Ultralytics caps output at `max_det` = 300. |
| 2.32 | Formula (6): `Conf_i = P_obj,i × IoU_i` (p. 47) | Not YOLOv8; see 2.23. |
| 2.33 | Formula (7): "A precision of 60.5%" (p. 48) | Not a result of this study; no four-class model exists. |
| 2.34 | Formula (8): "A recall of 50.6%" (p. 48) | Not a result of this study. |
| 2.35 | Formula (9): "The mAP@50 score of 53.9%" (p. 48); `mAP = ∫₀¹ p(r) dr` | Not a result of this study. The integral defines **AP** for one class; mAP is the mean of the per-class APs. |
| 2.36 | Formula (10): "An F1-Score of approximately 0.556" (p. 49) | Not a result of this study. It is also internally inconsistent: 2 × 0.605 × 0.506 / (0.605 + 0.506) = 0.551, not 0.556. |
| 2.37 | Formulas (11)–(17): "the system converts to corner-point format" and the letterbox description (pp. 50–51) | Both are done inside Ultralytics. The code reads `box.xyxy` directly (`video_processor.py:303`). Not wrong as theory, but "the system" overstates what this codebase does. |
| 2.38 | Formula (18): `t = f / FPS` | Correct form. Frame numbering starts at 1 (`video_processor.py:276`), giving a 1-frame offset. |
| 2.39 | Formulas (18)–(19): "GPS track points are typically recorded at 1 Hz" (p. 51) | On iOS the rate is not settable and must be reported as measured (`achievedHz`, `mobile/README.md:106`). Interpolation also clamps outside the track, which the text does not mention. |
| 2.40 | Formulas (20)–(21): "average inference time of approximately 200ms per frame on CPU … roughly 5 frames per second … 1,800 frames … approximately 6 minutes" (pp. 51–52) | Not measured. The model also does not run on all 1,800 frames: at 30 fps it runs on 300. All frames are still decoded, annotated and re-encoded, so T_total = N_frames × T_frame does not describe the pipeline. Measure with `/api/videos/export` (`videos.py:132`). |

### 3.4 Operational framework (pp. 52–55)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.41 | "with a maximum file size of 500 MB" (p. 53) | No size cap now (`app.py:24-26`). The 600 s duration cap (`app.py:27`) is not mentioned at all. |
| 2.42 | "recorded by a GPS logger or smartphone app" (p. 53) | The project's own mobile app now records both; see 2.53. |
| 2.43 | "system configuration parameters, including the confidence threshold setting (default 0.3), the NMS IoU threshold (default 0.5), and output format preferences" (p. 53) | Not user inputs. They are module constants (`video_processor.py:12-14`), and there is no output-format preference. |
| 2.44 | "decomposes the uploaded video into individual frames based on the video's native frame rate" (p. 53) | Sampled; see 2.13. |
| 2.45 | "(D10 Longitudinal Crack, D20 Transverse Crack, D30 Alligator Crack, D40 Pothole)" (p. 54) | Wrong codes. |
| 2.46 | "statistical reports and interactive dashboard … confidence score distributions, geographic distribution maps, and **severity assessments**" (p. 54) | Severity is not computed. The dashboard shows an average confidence, not a distribution (`DashboardPage.jsx:40`). |
| 2.47 | "exportable data in JSON …, CSV …, and PDF" (pp. 54–55) | No PDF. |

### 3.5 Use case (pp. 55–57)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.48 | "engineers who assess structural damage **severity**" (p. 55) | Severity is out of the system. |
| 2.49 | "The system serves two primary user roles" (p. 55) | The code has four roles (Section 0). |
| 2.50 | Use-case diagram (p. 56): two "Authenticate / Login" ellipses; System Administrator use cases "Manage User Accounts", "Manage Detections", "View System Logs" | The first is a duplicate. "Manage User Accounts" exists only as admin-only backend routes; its UI was removed and accounts are created directly in the database. There is no system-log feature. Inspection-status updates are available to every role that can open `/database`, not only admins (`App.jsx:18-20`). |
| 2.51 | The diagram omits real use cases | Missing: georeference a survey (control points), rename/delete a survey, view per-survey routes on the map, update inspection status, record a survey on the mobile app. |
| 2.52 | "sort by confidence level" (p. 55) | True: the Database page sorts by confidence (`DatabasePage.jsx:145`). |

### Missing from Chapter 3 entirely

**2.53 Mobile capture app.** Not in the chapter at all. It needs coverage in architecture,
inputs, data collection, positional-error factors, ethics (it logs the surveyor's own route) and
use cases.

**2.54 Georeferencing (manual control points).** Not in the chapter, and neither are
`position_source` or the clamping difference between the two positioning modes.

**2.55 Other features not mentioned:**

- Frame sampling and cross-frame deduplication.
- The 10-minute duration cap.
- Restart behaviour (interrupted processing is marked failed).
- The inspection-status workflow.
- Public reports.
- Raw-upload retention (30 days).

### 3.6 Respondents, 3.7 Ethics, 3.8 Statistical treatment (pp. 57–65)

| # | Claim (quoted) | Code / reality |
|---|---|---|
| 2.56 | "A target of [15 to 20] respondents" (p. 57) | Placeholder brackets are still in the text. |
| 2.57 | "Data is organized in user-specific contexts, ensuring that one user's uploaded survey data is not accessible to other users" (p. 59) | False for the map, database list/export/status, media streams, snapshots and report reads. See §1.8 and Q14. |
| 2.58 | "The SQLite database stores detection records with anonymized reference identifiers, and no personal information beyond the user's registered account credentials is linked to detection data" (pp. 59–60) | Detections link to `Video.user_id`. `User` stores full name, email, LGU and a government **ID photo** filename (`models.py:42-53`). `PublicReport` stores reporter name and contact (`:271-272`). |
| 2.59 | "The GPS data collected pertains strictly to public road locations and does not track or identify individual users" (p. 59) | A GPX from the mobile app is the surveyor's own timestamped route, stored per user (`GpsTrackPoint` → `Video.user_id`). It does track the person collecting the data. |
| 2.60 | "Data Handling and Retention … stored on secured, password-protected systems" (p. 61) | The default admin account is `admin` / `admin123`, created on first boot (`app.py:93-106`). Raw videos (which may contain faces and plates) and snapshots are stored unredacted. Copies can now leave controlled storage through the phone's Photos/Files export (`mobile/src/media.js`). |
| 2.61 | 3.8.1: "the four damage classes (D10, D20, D30, D40)" (p. 62) and 3.8.3 "(D10, D20, D30, D40)" (p. 65) | Wrong codes. |
| 2.62 | 3.8.1 "computed over the test dataset" (p. 62) | Objective 1 needs foreign and local test subsets reported separately (Section 3). The evaluation script uses `val` (`evaluate_model.py:32`). |
| 2.63 | 3.8.2 Standard deviation written as "σ = √[Σ(xᵢ − x̄)² / (N − 1)]" (p. 63) | That is the sample SD *s*, the same *s* used in the t-test. Use one symbol. |

---

## Section 3 — Consistency with the revised Chapters 1–2

### 3.1 Hypothesis (Ch1 §1.4, p. 7) and what Chapter 3 must therefore measure

> "…through its integration of a fine-tuned YOLOv8m detection model with GPS-to-video timestamp
> synchronization, will be effective in improving the detection, localization, and mapping of
> road damage … **as determined through evaluation by selected road maintenance personnel,
> engineers, and infrastructure administrators.**"

**What this means for Chapter 3.**

- The hypothesis is decided by **respondent evaluation**. So 3.8.2 (Likert means and the
  one-sample t-test against 3.41) is the test of the hypothesis, and Chapter 3 must say so
  explicitly.
- Model metrics and positional error answer RQ1 and RQ3. They do not decide the hypothesis.
- The hypothesis names a *fine-tuned YOLOv8m*. The runtime currently serves a YOLOv8n demo model
  (Section 0). Chapter 3 must commit to UAT being run on the fine-tuned four-class model.
- It names *GPS-to-video timestamp synchronization* only. Georeferenced surveys are a different
  positioning method; Chapter 3 must say whether they are included in the evaluation or excluded
  from it (Q8).

**Research questions** (p. 7) and the method Chapter 3 needs for each:

| RQ | Measured by | Method in current Chapter 3? |
|---|---|---|
| RQ1 detection | P, R, F1, mAP | Yes (3.8.1), but not split by subset (see Objective 1). |
| RQ2 does the log "correctly record the location, time, and type of each detection" | Correctness check of stored records | **No method.** Nothing in 3.8 checks that stored type, time and location are correct for a sample of detections. |
| RQ3 positional error and its factors | Haversine error (3.8.2) | Partly. The error metric is defined; the factor analysis is not (see Objective 3). |
| RQ4 efficiency vs. traditional manual inspection | Comparison against a manual baseline | **No method.** Likert perception items exist, but there is no time-on-task or manual-baseline comparison. |

### 3.2 Objectives (Ch1 §1.5, pp. 8–9)

**General objective.** "fine-tuned on the RDD2022 dataset and locally collected Philippine road
imagery". Chapter 3's Data Collection paragraph already matches this. The ML code has no
local-data path (§1.6).

**Objective 1** (requires precision, recall, F1 and mAP at IoU 0.50, "with results reported
separately for the foreign and local test subsets"):

- Chapter 3 p. 37 already says this. 3.8.1 does not, and must.
- Chapter 3 must define how each test subset is built. For the local set, it must split **by
  survey or route, not by frame**: adjacent frames are near-duplicates and would leak between
  train and test (Q4).
- The code holds an unstated acceptance bar, mAP@50 ≥ 0.50 on the local subset
  (`train_model.py:32`). It is in neither Chapter 1 nor Chapter 3 (Q5).

**Objective 3** names three factors: "GPS sampling rate, time offset, and video frame rate".
Chapter 3 must say how each is observed:

- GPS sampling rate: measured `achievedHz` per session (iOS cannot set it).
- Time offset: `time_offset`, clock skew and the measured video-start gap.
- Video frame rate: per video, `Video.fps`.

The code introduces further factors that Objective 3's "such as" covers but Chapter 3 should
name, or the error analysis will be incomplete:

- Inference sampling at 5 per second, which quantises the detection time.
- The 2-second deduplication window: which frame of a pothole's visibility becomes the record.
- Clamping outside the track.
- The 1-frame timestamp offset.

**Objective 4** (UAT relative to manual methods): needs the RQ4 method above.

### 3.3 Scope and limitations (Ch1 §1.7, pp. 10–11) — limits Chapter 3 must not exceed

**"frame-by-frame video analysis"** (p. 10). §1.2 (p. 5) also says "process uploaded videos
frame-by-frame". The code samples about 5 frames per second. Chapter 3 cannot describe sampling
without contradicting Chapter 1 (Q20).

**"video decoding, model inference, and GPS synchronization are all executed on a single
application server rather than on the user's device … does not support real-time roadside
detection or on-device inference"** (p. 11). This is consistent with a capture-only mobile app,
and Chapter 3 must keep the app strictly capture-only. The app does run local checks (GPS
filtering, the `time_offset` calculation, the movie completeness check). Chapter 3 should present
these as capture-quality checks, not processing.

**"trained primarily using the RDD2022 dataset supplemented with locally collected road
images"** (p. 11). Consistent.

**Not in Chapter 1's scope at all:**

- Manual georeferencing.
- Public (citizen) reports.
- The inspection-status workflow.
- The mobile app.

If Chapter 3 describes them, it goes beyond Chapter 1's scope. This needs either a Chapter 1
amendment or a decision to leave them out of Chapter 3 (Q7, Q9).

**Tense.** §1.1 (p. 3) states as present fact: "The detection model **is fine-tuned** on a
locally collected dataset of approximately 2,000 annotated frames … captured along national,
city, and barangay roads in Mendez-Nunez". Chapter 3 is proposal-tense, and the data has not been
collected. Chapter 3 should treat 2,000 as a target and keep "approximately". It should not
repeat the present tense.

### 3.4 Does Chapters 1–2 mention the mobile app?

**No**, not the project's own app.

- Every mention of "mobile" concerns other studies' on-device inference (Bustria et al. 2025;
  Dabous et al. 2025; iWatchRoad 2026).
- Chapter 2 argues against relying on mobile devices: "hardware limitations in mobile-device
  implementations, battery consumption, thermal throttling" (Synthesis, p. 21).
- §1.2 (p. 5) frames the system as "Instead of requiring real-time mobile-device processing,
  users may upload continuous road survey footage together with GPS track files".

**Implication for Chapter 3.** It must introduce the capture app as a **data-collection
instrument**, not a detection client, so the Chapter 2 argument still holds. Thermal behaviour
during *capture* is still relevant: the app keeps the screen awake and records 1080p for up to
10 minutes, and that test has not been run (Section 5).

### 3.5 Remaining D30, four-tier role, severity and pre-JWT references in Chapters 1–2

- **D30:** none. Chapters 1–2 use class names, never codes.
- **Four-tier roles** (barangay / municipal / provincial): none.
- **Severity:** only as future work (§1.6 "Future Researchers", p. 10: "adding damage severity
  classification"). Consistent.
- **Pre-JWT authentication:** none. Authentication is not discussed in Chapters 1–2.
- **Partner office:** consistent ("Mendez-Nunez, Cavite"; Ch3 §3.6 "Municipal Engineering Office
  of Mendez-Nunez"). The code uses "Mendez-Nuñez", with ñ (`app.py:97`). Pick one spelling.

### 3.6 Other Chapter 1–2 points Chapter 3 touches

**Title.** The thesis is titled "**OCULUBAK**". The code and repo docs call the system "Bantay
Kalsada". Chapter 3 must use one name (Q1).

**Albouchi et al. (2025)** is cited for *heat-map* visualisation (Ch2 pp. 16, 25). The map page
deliberately has no heatmap or clustering (`DamageMapPage.jsx`, project rule). Chapter 3 must not
claim a heatmap.

**Respondent types.** Chapter 1 lists road maintenance personnel, engineers and infrastructure
administrators. These are *respondent* types and are separate from the two *system* roles.
Chapter 3 should keep the two apart: three respondent groups, two system roles.

---

## Section 4 — Diagram inventory

**Format.** All new diagrams go in draw.io / diagrams.net mxGraph XML. In this pass only the
inventory and proposed structure are given. Existing sources: `Documents/diagrams/*.png` (raster
images of the current figures, no editable source) and `figures/*.mmd` (Mermaid, not draw.io, and
not used in the PDF).

| # | Figure | Current state | What must change | New file needed |
|---|---|---|---|---|
| F1 | Agile methodology (Fig. 3.1, p. 29) | Generic stock wheel; no phases | Redraw as five named sprints in sequence: (1) System Foundation and Core Development, (2) Detection Refinement and Feature Expansion, (3) Geospatial Integration and Data Synchronization, (4) System Integration and Interface Enhancement, (5) Optimization and Validation. Each sprint passes Plan → Design → Develop → Test → Review, with the review feeding the next sprint. Show 3.1.6 future work as a separate, dashed group, which the text already claims the figure has. | Yes |
| F2 | Conceptual framework, IPO (currently Fig. 3.4, p. 52) | Raster; lists "System configuration parameters" as input and "severity" in the text | Moves to 3.2 under the conceptual/operational swap. Inputs: survey video (+ optional GPX/CSV with `time_offset`, or control points), login. Process: sampled inference → cross-frame dedup → positioning (GPS sync or control points) → annotation. Outputs: annotated video, geo-located log (type, time, coordinates, `position_source`), map, CSV/JSON export. Remove configuration-parameter inputs, PDF and severity. | Yes |
| F3 | Detailed end-to-end pipeline (currently Fig. 3.2.1, p. 35) | Raster; D30; 0.3 / 0.5; per-frame; PDF; 26,620 | Moves to 3.4. Two lanes: **Training** (RDD2022 four-class subset + local set → per-class cap → foreign/local splits → YOLOv8m fine-tune → per-subset evaluation) and **Operation** (capture → upload → sample every `fps/5` frame → inference at conf 0.15 / IoU 0.45, or whatever Q3 decides → dedup → positioning branch: GPS interpolation with clamping vs control points without → store → annotate → ffmpeg H.264). Any number not measured is shown as a symbol, not a value. | Yes |
| F4 | System architecture (Fig. 3.2.2, p. 40) | Raster; three tiers; no mobile; wrong weights file | Must include the mobile capture client. **Proposed structure: still three tiers, with two clients in the presentation tier** (web SPA; mobile capture app with its local storage and upload queue). Application tier: Flask API + JWT middleware, video processing thread, GPS sync service, georeferencing service, ffmpeg. Data tier: SQLite, file storage (uploads, processed, snapshots), fine-tuned weights. The **offline training pipeline** sits outside the runtime tiers, joined by a dashed "weights" arrow. Drawn as a separate tier, the mobile app makes it **four**; recommendation is three tiers with two clients, because the app has no business logic (see Q-F4). | Yes |
| F5 | YOLOv8m architecture (Fig. 3.3.1, p. 42) | Raster; D30 in head labels; "objectness" implied in text; typos; duplicated label row | Redraw: backbone (Conv, C2f, SPPF) → neck (PAN-FPN with C2f/upsample/concat) → three decoupled heads (P3/P4/P5), each with a cls branch (4 classes, BCE) and a box branch (DFL + CIoU). No objectness. Label the classes D00 / D10 / D20 / D40. Input size as a symbol or the value chosen in Q2. | Yes |
| F6 | Use case (Fig. 3.5.1, p. 56) | Raster; duplicate Login; "View System Logs" does not exist | **Two actors**: Road Maintenance Personnel, System Administrator. RMP: Log in; Record survey (mobile app); Upload survey video (+GPS); Monitor processing; View detection results / annotated video; Georeference survey (control points); View damage map; Update inspection status; Filter/sort detections; Export CSV/JSON; Rename/delete own survey. Admin: everything RMP can do (generalisation arrow) plus Manage user accounts (only if Q6 says it stays; there is currently no UI). Drop "View System Logs", the duplicate Login and PDF. The «include» to Login is better shown as a precondition or left out. | Yes |
| F7 | Formula figures 3.3.2a / b / c (pp. 45, 47, 50) | **Raster images** (`Documents/diagrams/3.3_formulas_*.png`) of typeset equations; contain wrong content (b = 16, Conf = P_obj × IoU, mAP integral) | These are equations, not diagrams. **Recommendation: render them as native Word equations (OMML)**, numbered (1)…(n) on the right, so they stay editable and searchable. If a draw.io source is required anyway, draw.io supports LaTeX through its MathJax option, but the result is still an image in Word (Q16). | Rewrite as equations |
| F8 | State diagram (`Documents/diagrams/3.5_state_diagram.png`) | Exists as a file; not in the chapter | Optional. If kept, use the real video states `uploaded → processing → completed / failed` (failed also on restart) and the detection states `pending_validation → inspected → scheduled → ongoing_repair → resolved`. | Optional |

### Numbering and caption inconsistencies found

| Figure | Number style | Separator | Caption position | Italic |
|---|---|---|---|---|
| 3.1 Agile (p. 28) | two-level | none | above; image on next page | no |
| 3.2.1 Conceptual (p. 34) | three-level | none | above; image on next page | yes |
| 3.2.2 Architecture (p. 39) | three-level | none | above; a blank page separates it from the image (p. 40) | yes |
| 3.3.1 YOLOv8m (p. 41) | three-level | none | above; image on next page | yes |
| 3.3.2a (p. 44) | three-level + letter | colon | above | yes |
| 3.3.2b (p. 46) | three-level + letter | colon | above | yes |
| 3.3.2c (p. 50) | three-level + letter | colon | **below** | yes |
| 3.4 IPO (p. 52) | two-level | none | above | yes |
| 3.5.1 Use case (p. 56) | three-level | none | above | yes |
| Algorithm "1" (p. 43) | not chapter-scoped | colon | above | no |
| Tables: synthesis (2.3.1), interpretation scale (p. 64), software tools (p. 65) | **unnumbered** | — | — | — |

**Proposed single scheme.**

- **Figures:** `Figure 3.N. Title in sentence case`. Sequential within the chapter, independent
  of section numbers (3.1, 3.2, 3.3 …). Placed **below** the figure, italic title, on the same
  page as the figure.
- **Tables:** `Table 3.N. Title`, placed **above** the table.
- **Algorithms:** `Algorithm 3.N. Title`, above.
- **Equations:** `(N)` right-aligned, numbered consecutively through the chapter.
- One style everywhere: number in bold, then a period, then the title. No colons.

Check this against the DLSU-D CSCS format guide if one exists (Q15). The scheme above is a
proposal, not the department's rule.

---

## Section 5 — Cannot be written yet

| Chapter 3 item | Missing | What unblocks it |
|---|---|---|
| Dataset counts (RDD2022 subset per class, after cap) | The scripts have not been run on the real download; "26,620" has no source | Run `download_rdd2022.py` / `dataset_prep.py` with the chosen cap; record per-class and per-split counts from the generated `data.yaml` notes. |
| Local dataset (frames, per class, routes, split) | Not collected; ethics clearance comes first | Ethics approval → field capture → frame extraction rule → annotation → split by survey (Q4). Annotation protocol also needed: tool, annotators, agreement check. |
| Final training configuration and run details (epochs actually run, hardware, time) | Four-class model not trained; two conflicting configs | Q2, then train. |
| Evaluation results (P, R, F1, mAP@50 per class, foreign vs. local, confusion matrix) | No four-class model; no per-subset evaluation script | Train, then add a test-split, per-subset evaluation (`evaluate_model.py` currently uses `val`). |
| Calibrated confidence threshold | No calibration procedure exists; code uses 0.15 | Define the procedure (for example, maximise F1 on val) or drop the word "calibrated" (Q3). |
| Measured positional error (mean, SD, max, n) | No field validation; no tooling | Field reference points (method per Q10), then Haversine against stored coordinates. Separate GPS-file from georeferenced surveys. |
| Measured video-start gap | Not measured | Stopwatch test (`mobile/README.md` device tests): first-frame time vs. GPX `videoStart`. |
| Measured iOS GPS rate and gaps | Not measured | `achievedHz` and gap counts from each session's GPX metadata, across real survey runs. |
| Measured clock skew | Not measured | `clockSkewMs` from GPX metadata. |
| Measured capture frame rate and bitrate on the iPhones used | Not measured; the iPhone 16 file size suggests the 5 Mbit/s request is not applied | `Video.fps` / `file_size` / `duration` from uploads, or `ffprobe`; per device model. |
| Thermal test outcome | Not run | Windshield mount, 590 s at midday, per device. |
| Processing throughput (Formulas 20–21) | Not measured; the "200 ms on CPU" has no source | `/api/videos/export` on the evaluation hardware with the final weights; state the hardware. |
| UAT results | Not run; respondent count still "[15 to 20]" | Ethics → recruitment → instrument → administration. The questionnaire items themselves are not in Chapter 3 (only the dimensions). |
| RQ2 record-correctness check | No method | Define a sample-and-verify procedure for type, time and location of stored detections. |
| RQ4 efficiency vs. manual inspection | No method, no baseline | Define the manual baseline (for example, time to inspect and document a fixed route manually vs. with the system) and how it is measured. |
| Mobile end-to-end verification | Device checklist unchecked; save fix not yet confirmed | Complete `mobile/README.md:122-136` on the evaluation iPhones. |
| Android | Untested | Only needed if Chapter 3 mentions Android. Otherwise state iPhone-only capture. |

---

## Section 6 — Questions that need a human answer

1. **System name.** "OCULUBAK" (thesis title) or "Bantay Kalsada" (code)? Is one the other's
   subtitle?
2. **Training configuration of record.** `train_model.py` (100 epochs, batch 16, imgsz 640,
   AdamW) or `train_local.py` (150, batch 4, imgsz 1024, auto)? The current `best.pt` came from
   the second. Chapter 3's Formula (1), Formula (2), the pipeline figure and the YOLO figure all
   depend on this.
3. **Thresholds.** Is Chapter 3 proposing conf 0.15 / IoU 0.45 (code) or 0.3 / 0.5 (current
   text)? Is "calibrated on validation results" a real planned step? If so, by what criterion?
4. **Local split.** 70/15/15 (code comment) or 80/15/5? How are the foreign and local test
   subsets formed? Do you agree the local split must be by survey or route, not by frame?
5. **Acceptance bar.** Should mAP@50 ≥ 0.50 on the local test subset (`train_model.py:32`) be
   stated in Chapter 3? It is not in Chapter 1.
6. **Roles.** Chapter 3 will say two roles; the code has four. Will the code be collapsed to two
   (your backend workstream), or does Chapter 3 describe two *conceptual* roles that map onto the
   code's four? Does "Manage user accounts" stay as an admin use case even though it has no UI?
7. **Out-of-scope features.** Public reports, the inspection-status workflow, survey
   rename/delete: describe them in Chapter 3, or leave them out to stay within §1.7?
8. **Georeferencing in the evaluation.** Are hand-georeferenced surveys part of the positional
   error study (reported separately), or used only as an operational fallback and excluded?
9. **Mobile app and Chapter 1.** Chapter 1 never mentions it, and §1.2 frames inputs as uploaded
   footage plus GPS files. Is the app *the* capture method for the study's data, or one option?
   Does Chapter 1 get amended (outside this pass)?
10. **Ground truth for positional error.** §3.8.2 proposes a "handheld GPS receiver or smartphone
    GPS application" for reference points. A phone's error is about the same size as the error
    being measured. Use a better reference (survey-grade receiver, or points identified on
    orthophotos), or accept and state the limitation?
11. **Upload size cap.** Currently off (changed 2026-10-08 because iPhone 16 recordings exceeded
    500 MB). What does Chapter 3 state as the limit? Should the bitrate issue be fixed first, so
    the stated 1080p / 5 Mbit/s is true?
12. **Demo model.** `app.py:34` serves an external YOLOv8n model. Confirm that UAT and every
    reported number will use the project's fine-tuned four-class YOLOv8m only.
13. **PDF export.** Implement it, or remove PDF from Chapter 3 (and from the output lists in
    3.2.1, 3.4 and the use cases)?
14. **Ethics vs. data access.** The claim that one user's data is invisible to others is false in
    the code (§1.8). Change the code to scope by user (or by LGU), or change the ethics text? The
    same question applies to the ID-photo and reporter-contact fields, the default admin
    password, unredacted raw video, and phone-side copies.
15. **Caption format.** Does DLSU-D CSCS have a required figure/table/equation style? If not, is
    the scheme in Section 4 acceptable? Which figure did the brief mean by "no caption at all"?
16. **Formula figures.** Native Word equations (recommended) or draw.io with MathJax?
17. **Respondent count.** Replace "[15 to 20]" with what number, and on what basis?
18. **"City roads".** §1.1 says data comes from "national, city, and barangay roads in
    Mendez-Nunez". Mendez is a municipality. Should this read "municipal roads"? (Chapter 1
    wording; reported only.)
19. **RQ4 method.** What counts as the manual-inspection baseline, and is it measured (time,
    coverage) or only perceived (Likert)?
20. **"Frame-by-frame".** Chapter 1 (§1.2, §1.7) says frame-by-frame; the code samples about 5
    frames per second. Change the code to infer every frame, or reword Chapter 1 to "sampled
    frames"? Chapter 3 cannot be correct against both.
- **Q-F4. Architecture tiers.** Three tiers with two clients (recommended), or a separate fourth
  "capture" tier for the mobile app?
