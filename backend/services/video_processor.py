"""Video processing service — YOLOv8 road damage detection pipeline with GPS sync."""

import os
import cv2
import uuid
import numpy as np
from datetime import datetime, timezone


# Inference settings. These are the numbers the thesis cites (Sec 3.2.1, 3.4, Algorithm 1);
# change them here only so the paper and the code cannot drift apart.
INFERENCE_FPS = 5        # frames analysed per second of video — every (fps / INFERENCE_FPS)-th frame
CONF_THRESHOLD = 0.15    # minimum confidence for a prediction to be kept
IOU_THRESHOLD = 0.45     # non-maximum-suppression overlap threshold
# Model input size (longest side, pixels). At Ultralytics' default of 640 a 1920-pixel phone frame
# is shrunk to a third, and a pothole 20-40 m ahead is a few pixels wide: on a 3.5-minute
# windshield survey the model returned 13 boxes at 640 and 157 at 1280. Costs about twice the
# time of 640 here, because only the road band (below) is passed to the model.
INFERENCE_IMGSZ = 1280
# Road band: the strip of the picture between the horizon and the bonnet (or the bottom edge),
# as fractions of the frame height from the top. Only this strip is passed to the model, so
# buildings, trees, sky and the vehicle's own bonnet are never looked at. The phone app records
# both lines per survey from its camera screen, where the user lines them up with the horizon
# and the bonnet of the vehicle it is mounted in (Video.road_top / road_bottom). These defaults
# apply to surveys without them (web uploads): horizon at the middle, nothing cut off below.
ROAD_REGION_TOP = 0.5
ROAD_REGION_BOTTOM = 1.0
ROAD_REGION_MIN = 0.1    # a band thinner than this (fraction of the height) is ignored as a mistake


def road_band(top, bottom):
    """The road band to use, as (top, bottom) fractions: the given values when they make sense,
    else the defaults. Used by the upload route (to store) and the pipeline (to apply)."""
    try:
        top = ROAD_REGION_TOP if top is None else min(max(float(top), 0.0), 1.0)
        bottom = ROAD_REGION_BOTTOM if bottom is None else min(max(float(bottom), 0.0), 1.0)
    except (TypeError, ValueError):
        return ROAD_REGION_TOP, ROAD_REGION_BOTTOM
    if bottom - top < ROAD_REGION_MIN:
        return ROAD_REGION_TOP, ROAD_REGION_BOTTOM
    return top, bottom

# Model class name -> (RDD2022 code, label). Codes follow CRDDC 2022 (Arya et al., 2022):
# D00 longitudinal, D10 transverse, D20 alligator, D40 pothole. There is no D30.
# Substring keys let any reasonably named model map without code changes.
DAMAGE_CLASS_MAP = {
    'd00': ('D00', 'Longitudinal Crack'),
    'd10': ('D10', 'Transverse Crack'),
    'd20': ('D20', 'Alligator Crack'),
    'd40': ('D40', 'Pothole'),
    'longitudinal': ('D00', 'Longitudinal Crack'),
    'transverse': ('D10', 'Transverse Crack'),
    'lateral': ('D10', 'Transverse Crack'),
    'alligator': ('D20', 'Alligator Crack'),
    'crocodile': ('D20', 'Alligator Crack'),
    'pothole': ('D40', 'Pothole'),
}

# Colors for each damage type (BGR format for OpenCV)
DAMAGE_COLORS = {
    'D00': (255, 165, 0),    # Orange — Longitudinal
    'D10': (0, 255, 255),    # Yellow — Transverse
    'D20': (0, 0, 255),      # Red — Alligator
    'D40': (0, 69, 255),     # Dark Orange — Pothole
}


# Phones save a recording held sideways or upside down with a rotation flag, not rotated
# pixels. Browsers honour the flag; OpenCV reports it (CAP_PROP_ORIENTATION_META) but by default
# hands over the frames as stored. Same mapping OpenCV's own auto-rotation uses.
_ROTATIONS = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}


def open_upright(path):
    """Open a video for upright reading. Returns (cap, rotate_code or None, width, height),
    with width/height as displayed. Apply cv2.rotate(frame, rotate_code) to every frame read.
    We rotate ourselves (auto-rotation off) so the output size is known before the first frame.
    """
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)
    angle = int(round(cap.get(cv2.CAP_PROP_ORIENTATION_META) or 0)) % 360
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if angle in (90, 270):
        width, height = height, width
    return cap, _ROTATIONS.get(angle), width, height


class ModelUnavailable(Exception):
    """The model file cannot be used. Its message is shown to the user as the failure reason."""


def model_file_problem(model_path):
    """Plain-language reason the model file is unusable, or None. Checked at startup and per run.

    A Git LFS placeholder is the common case: a clone without `git lfs pull` has a ~130-byte
    text file where the weights should be, and every analysis then fails at 0%.
    """
    name = os.path.relpath(model_path, os.path.join(os.path.dirname(__file__), '..', '..'))
    if not os.path.exists(model_path):
        return f'The detection model {name} is missing on the server.'
    with open(model_path, 'rb') as f:
        head = f.read(64)
    if head.startswith(b'version https://git-lfs'):
        return (f'The detection model on the server ({name}) was never downloaded: it is a Git LFS '
                'placeholder. On the server computer run "git lfs pull" in the project folder '
                '(or run the installer again), then choose "Analyse again" on the survey.')
    return None


def process_video(video_id, config):
    """
    Process an uploaded video:
    1. Sample frames at INFERENCE_FPS
    2. Run YOLOv8 inference on each sampled frame
    3. Assign GPS coordinates via timestamp synchronization
    4. Draw bounding boxes on detections
    5. Reassemble annotated video
    6. Save detection records to database
    """
    from models import db, Video, Detection

    video = Video.query.get(video_id)
    if not video:
        print(f"❌ Video {video_id} not found")
        return

    print(f"🔄 Starting processing for video: {video.original_filename}")

    # Update status
    video.status = 'processing'
    video.processing_progress = 0
    video.error_message = None
    db.session.commit()

    try:
        # Load YOLOv8 model
        model = _load_model(config['MODEL_PATH'])

        # Load GPS track if available
        gps_points = _load_gps_track(video, config)

        # Fallback: manually placed control points (only when there is no GPS track)
        control_points = None
        if gps_points is None and len(video.control_points) >= 2:
            control_points = list(video.control_points)
            print(f"📍 Using {len(control_points)} manual control points for georeferencing")

        # Process video
        input_path = os.path.join(config['UPLOAD_FOLDER'], video.filename)
        processed_filename = f"processed_{video.filename}"
        output_path = os.path.join(config['PROCESSED_FOLDER'], processed_filename)
        snapshots_dir = config['SNAPSHOTS_FOLDER']

        detections, actual_filename = _run_detection_pipeline(
            model, input_path, output_path, snapshots_dir,
            video_id, video, db, gps_points, control_points
        )

        if actual_filename is None:
            raise Exception("Failed to create video file")

        # Severity scoring is future work (thesis Sec 3.1.6). services/severity_service.py is kept
        # for reference but nothing calls it; the app records damage type and position only.

        # Update video record with actual processed filename (may differ due to codec)
        video.status = 'completed'
        video.processing_progress = 100
        video.processed_filename = actual_filename
        video.processed_date = datetime.now(timezone.utc)
        video.total_detections = len(detections)
        db.session.commit()

        damage_summary = _summarize_detections(detections)
        print(f"✅ Processing complete: {len(detections)} damages detected {damage_summary}")

    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        video.status = 'failed'
        video.processing_progress = 0
        # Shown to the user (web survey page, phone survey list). Known causes get their own
        # sentence; anything else is reported as an internal error with the details in the log.
        video.error_message = (str(e) if isinstance(e, ModelUnavailable)
                               else 'The server hit an error while analysing this survey. '
                                    'The details are in the server log.')[:500]
        db.session.commit()


def _load_model(model_path):
    """Load YOLOv8 model, falling back to pretrained if custom model not found."""
    from ultralytics import YOLO

    problem = model_file_problem(model_path)
    if problem and os.path.exists(model_path):
        raise ModelUnavailable(problem)
    if os.path.exists(model_path):
        print(f"📦 Loading custom model from: {model_path}")
        model = YOLO(model_path)
    else:
        print("⚠️  Custom model not found. Using pretrained YOLOv8n as fallback.")
        print("   Train a custom model using ml/train_model.py for better accuracy.")
        model = YOLO('yolov8n.pt')

    return model


def _load_gps_track(video, config):
    """Load and parse GPS track file if available."""
    if not video.gps_filename:
        print("📍 No GPS track file provided — detections will not have coordinates")
        return None

    gps_path = os.path.join(config['UPLOAD_FOLDER'], video.gps_filename)
    if not os.path.exists(gps_path):
        print(f"⚠️  GPS file not found: {gps_path}")
        return None

    try:
        from services.gps_service import parse_gps_file, validate_gps_track

        gps_points = parse_gps_file(gps_path)
        validation = validate_gps_track(gps_points, video.duration or 0)

        print(f"🛰️  GPS track loaded: {validation['message']}")

        if not validation['valid']:
            print(f"⚠️  GPS track validation failed: {validation['message']}")
            return None

        # Store GPS track points in database
        from models import GpsTrackPoint, db as models_db
        for pt in gps_points:
            track_point = GpsTrackPoint(
                video_id=video.id,
                timestamp=pt['timestamp'],
                latitude=pt['latitude'],
                longitude=pt['longitude'],
                elevation=pt.get('elevation'),
            )
            models_db.session.add(track_point)
        models_db.session.commit()
        print(f"📍 Stored {len(gps_points)} GPS track points in database")

        return gps_points

    except Exception as e:
        print(f"⚠️  Failed to load GPS track: {str(e)}")
        return None


def _classify_damage(class_name, cls_id, model):
    """Classify the detection into damage type and label.
    
    Returns:
        tuple: (damage_code, damage_label, is_damage)
    """
    name_lower = class_name.lower().strip()

    # Direct mapping from model class names
    for key, (code, label) in DAMAGE_CLASS_MAP.items():
        if key in name_lower:
            return code, label, True

    # For custom model with few classes — assume all are damage types
    if len(model.names) <= 5:
        # Fall back to class index in the CRDDC 2022 order used by ml/dataset_prep.py
        rdd_map = {0: ('D00', 'Longitudinal Crack'), 1: ('D10', 'Transverse Crack'),
                   2: ('D20', 'Alligator Crack'), 3: ('D40', 'Pothole')}
        if len(model.names) == 1:
            return 'D40', 'Pothole', True  # single-class (pothole-only) models
        if cls_id in rdd_map:
            return rdd_map[cls_id][0], rdd_map[cls_id][1], True
        return 'D40', 'Pothole', True

    # For pretrained COCO model (fallback) — no direct damage classes
    return 'D40', 'Pothole', False


def _run_detection_pipeline(model, input_path, output_path, snapshots_dir, video_id, video, db,
                            gps_points=None, control_points=None):
    """Run frame-by-frame detection and generate annotated video."""
    from models import Detection
    from services.gps_service import interpolate_gps
    from services.georeference_service import interpolate_from_control_points
    from services.damage_tracker import DamageTracker, drop_fixed_spots
    from services import damage_verifier

    cap, rotate, width, height = open_upright(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Ensure dimensions are even (required by most video codecs)
    width = width - (width % 2)
    height = height - (height % 2)

    print(f"📹 Video info: {width}x{height} @ {fps} fps, {total_frames} frames"
          + (" (rotated upright from the phone's orientation flag)" if rotate is not None else ""))

    # === VIDEO WRITER SETUP ===
    # Strategy: Use OpenCV MJPG writer (fast, hardware-optimized) to write AVI,
    # then convert to MP4 with FFmpeg afterwards. This is much faster than piping
    # raw frames to FFmpeg because MJPG is ~50x smaller than raw BGR24.
    import subprocess
    import shutil

    ffmpeg_available = shutil.which('ffmpeg') is not None

    out = None
    ffmpeg_proc = None
    output_filename = output_path

    # Use OpenCV VideoWriter with MJPG codec (fast and reliable)
    codec_options = [
        ('MJPG', '.avi', 'Motion JPEG AVI'),
        ('XVID', '.avi', 'XVID AVI'),
    ]
    for codec_name, ext, description in codec_options:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec_name)
            test_output = output_path.rsplit('.', 1)[0] + ext
            test_writer = cv2.VideoWriter(test_output, fourcc, fps, (width, height))
            if test_writer.isOpened():
                out = test_writer
                output_filename = test_output
                print(f"✅ Using codec: {description} ({codec_name})")
                break
            else:
                test_writer.release()
        except Exception as e:
            continue

    if out is None:
        print(f"❌ Failed to initialize video writer with ANY codec")
        cap.release()
        return [], None

    all_detections = []
    frame_number = 0
    process_every_n = max(1, int(fps / INFERENCE_FPS))  # sample ~INFERENCE_FPS frames per second

    tracker = DamageTracker(fps)
    band_top, band_bottom = road_band(video.road_top, video.road_bottom)
    road_top_px = int(height * band_top)
    road_bottom_px = int(height * band_bottom)
    print(f"🛣️  Road band: {band_top:.0%}–{band_bottom:.0%} of the frame height, model input {INFERENCE_IMGSZ}px")
    finished_tracks = []

    def snapshot_track(track):
        """Write a finished track's snapshot now, so its frame copy is not held until the end."""
        best = track.best
        # The AI check looks at the clean frame, before the box and its label are drawn on it.
        track.ai_score = damage_verifier.score(track.best_image, best['box'])
        track.snapshot = f"snap_{video_id}_{best['frame']}_{track.id}.jpg"
        snap_frame = track.best_image
        _draw_detection(snap_frame, *best['box'], best['conf'], best['code'], best['label'], best['color'])
        cv2.imwrite(os.path.join(snapshots_dir, track.snapshot), snap_frame)
        track.best_image = None   # free the frame copy
        finished_tracks.append(track)

    def save_track(track):
        """Store one damage from its best sighting: that frame's box, time, position and snapshot."""
        best = track.best
        best_frame = best['frame']
        x1, y1, x2, y2 = best['box']

        # Formula 18: t_frame = frame_number / FPS
        timestamp = float(best_frame) / float(fps)

        # GPS Synchronization (Formula 19)
        latitude = None
        longitude = None
        position_source = 'none'
        if gps_points:
            gps_coord = interpolate_gps(gps_points, timestamp, time_offset)
            if gps_coord:
                latitude = gps_coord['latitude']
                longitude = gps_coord['longitude']
                position_source = 'gps_file'
        elif control_points:
            # Manual control points — piecewise between bracketing points, no clamping
            cp_coord = interpolate_from_control_points(control_points, timestamp)
            if cp_coord:
                latitude, longitude = cp_coord
                position_source = 'georeferenced'

        snapshot_name = track.snapshot

        detection = Detection(
            video_id=video_id,
            frame_number=best_frame,
            timestamp=timestamp,
            confidence=best['conf'],
            bbox_x1=x1, bbox_y1=y1, bbox_x2=x2, bbox_y2=y2,
            frame_snapshot=snapshot_name,
            damage_type=best['code'],
            damage_label=best['label'],
            latitude=latitude,
            longitude=longitude,
            position_source=position_source,
            road_name=video.road_name,
            source_type='ai_detection',
            ai_check_score=track.ai_score,
        )
        db.session.add(detection)
        all_detections.append(detection)

    active_boxes = {}
    box_persistence = int(fps * 0.5)

    time_offset = video.time_offset or 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if rotate is not None:
            frame = cv2.rotate(frame, rotate)
        if frame.shape[0] != height or frame.shape[1] != width:
            # The writer silently drops any frame of another size (odd dimensions were trimmed).
            frame = frame[:height, :width]

        frame_number += 1

        if frame_number % 30 == 0:
            progress = (frame_number / total_frames) * 100
            video.processing_progress = min(progress, 99)
            db.session.commit()

        expired_ids = [bid for bid, box_info in active_boxes.items() if frame_number > box_info['end_frame']]
        for bid in expired_ids:
            del active_boxes[bid]

        if frame_number % process_every_n == 0:
            active_boxes.clear()

            # Only the road band goes to the model; its boxes are moved back into frame coordinates.
            band = frame[road_top_px:road_bottom_px]
            results = model(band, verbose=False, conf=CONF_THRESHOLD, iou=IOU_THRESHOLD, imgsz=INFERENCE_IMGSZ)
            sightings = []

            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = model.names[cls_id].lower() if cls_id < len(model.names) else ''

                        damage_code, damage_label, is_damage = _classify_damage(class_name, cls_id, model)

                        if is_damage or _is_pothole_class(class_name, cls_id, model):
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            y1, y2 = y1 + road_top_px, y2 + road_top_px

                            box_id = f"{frame_number}_{int(x1)}_{int(y1)}"
                            damage_color = DAMAGE_COLORS.get(damage_code, (0, 69, 255))
                            active_boxes[box_id] = {
                                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                                'conf': conf,
                                'end_frame': frame_number + box_persistence,
                                'damage_code': damage_code,
                                'damage_label': damage_label,
                                'color': damage_color,
                            }

                            sightings.append({
                                'frame': frame_number,
                                'box': (float(x1), float(y1), float(x2), float(y2)),
                                'conf': conf,
                                'code': damage_code,
                                'label': damage_label,
                                'color': damage_color,
                            })

            # One record per damage: sightings are joined into tracks, and a track is finished once
            # it leaves the view; it is stored from its best sighting (services/damage_tracker.py).
            for track in tracker.update(frame_number, sightings, frame):
                snapshot_track(track)

        # Mark the road band on the annotated video, so viewers see what was analysed.
        cv2.line(frame, (0, road_top_px), (width, road_top_px), (255, 255, 255), 1, cv2.LINE_AA)
        if road_bottom_px < height:
            cv2.line(frame, (0, road_bottom_px), (width, road_bottom_px), (255, 255, 255), 1, cv2.LINE_AA)

        for box_info in active_boxes.values():
            _draw_detection(frame, box_info['x1'], box_info['y1'],
                            box_info['x2'], box_info['y2'], box_info['conf'],
                            box_info.get('damage_code', 'D40'),
                            box_info.get('damage_label', 'Pothole'),
                            box_info.get('color', (0, 69, 255)))

        # Write frame to output
        out.write(frame)

    cap.release()

    # Damage still in view when the video ends.
    for track in tracker.finish_all():
        snapshot_track(track)
    # What stays at one spot in the picture is on the windshield or the vehicle, not the road.
    kept, fixed = drop_fixed_spots(finished_tracks, fps)
    for track in fixed:
        try:
            os.remove(os.path.join(snapshots_dir, track.snapshot))
        except OSError:
            pass
    if fixed:
        print(f"🪟 Dropped {len(fixed)} detections fixed to the camera (windshield reflection, bonnet)")
    for track in kept:
        save_track(track)
    if damage_verifier.problem():
        print(f"⚠️  AI check skipped: {damage_verifier.problem()}")
    else:
        flagged = sum(1 for t in kept if t.ai_score is not None and t.ai_score < damage_verifier.VERIFY_THRESHOLD)
        print(f"🔎 AI check: {flagged} of {len(kept)} detections flagged as likely not road damage")
    all_detections.sort(key=lambda d: d.frame_number)

    # Finalize video output
    if out:
        out.release()

    # Verify output file exists
    import time
    max_wait = 5
    wait_time = 0
    while wait_time < max_wait and (not os.path.exists(output_filename) or os.path.getsize(output_filename) == 0):
        time.sleep(0.1)
        wait_time += 0.1

    if not os.path.exists(output_filename):
        print(f"❌ Video file was not created: {output_filename}")
        return [], None

    file_size = os.path.getsize(output_filename)
    if file_size == 0:
        print(f"❌ Video file is empty: {output_filename}")
        return [], None

    print(f"✅ Video file created: {os.path.basename(output_filename)} ({file_size:,} bytes)")

    # If we used OpenCV fallback (AVI), convert to MP4 for browser playback
    if output_filename.endswith('.avi') and ffmpeg_available:
        mp4_path = output_filename.replace('.avi', '.mp4')
        conversion_success = _convert_avi_to_mp4(output_filename, mp4_path)
        if conversion_success:
            try:
                os.remove(output_filename)
                output_filename = mp4_path
                print(f"✅ Using converted MP4: {os.path.basename(output_filename)}")
            except Exception as e:
                print(f"⚠️  Could not delete AVI ({e}), keeping both files")
        else:
            print(f"📹 Using AVI format (browser may not play): {os.path.basename(output_filename)}")

    db.session.commit()

    actual_filename = os.path.basename(output_filename)
    print(f"📹 Output video: {actual_filename}")

    return all_detections, actual_filename


def _summarize_detections(detections):
    """Create a summary string of detection counts by type."""
    counts = {}
    for d in detections:
        label = d.damage_label or 'Unknown'
        counts[label] = counts.get(label, 0) + 1
    if not counts:
        return ""
    parts = [f"{count} {label}" for label, count in sorted(counts.items())]
    return f"({', '.join(parts)})"


def _is_pothole_class(class_name, cls_id, model):
    """Check if detection class represents a pothole."""
    if len(model.names) <= 5:
        return True

    # Only rescue classes that name one of the four CRDDC 2022 codes. Generic names such as
    # 'crack', 'block' or 'edge' are NOT in the scheme: _classify_damage cannot place them, so
    # keeping them here would file them under D40 and show a plain crack as a pothole. Dropping
    # them keeps the app honest about the four classes it claims to detect.
    pothole_keywords = ['pothole', 'hole', 'd40', 'd00', 'd10', 'd20']
    return any(kw in class_name for kw in pothole_keywords)


def _draw_detection(frame, x1, y1, x2, y2, confidence, damage_code='D40',
                    damage_label='Pothole', color=(0, 69, 255)):
    """Draw a styled bounding box and label on the frame with damage type info."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

    # Adjust color intensity by confidence
    if confidence > 0.7:
        alpha = 1.0
    elif confidence > 0.5:
        alpha = 0.85
    else:
        alpha = 0.7

    display_color = tuple(int(c * alpha) for c in color)

    # Draw thick bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), display_color, 3)

    # Draw filled background for label
    label = f"{damage_label} {confidence:.0%}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

    cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), display_color, -1)
    cv2.putText(frame, label, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), thickness)

    # Draw corner markers for style
    corner_len = 15
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), display_color, 4)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), display_color, 4)
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), display_color, 4)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), display_color, 4)
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), display_color, 4)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), display_color, 4)
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), display_color, 4)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), display_color, 4)


def _convert_avi_to_mp4(avi_path, mp4_path):
    """Convert AVI video to MP4 container using H.264 encoding for browser compatibility.
    
    Uses CRF 18 for near-lossless quality (lower = higher quality, 0 = lossless).
    Previous CRF 28 caused visible blur.
    """
    import subprocess
    try:
        print(f"🔄 Re-encoding AVI to MP4 H.264 (CRF 18, high quality)...")

        result = subprocess.run([
            'ffmpeg', '-y', '-i', avi_path,
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-crf', '18',
            '-pix_fmt', 'yuv420p',
            '-movflags', '+faststart',
            mp4_path
        ], capture_output=True, text=True, timeout=600)

        if result.returncode == 0 and os.path.exists(mp4_path):
            mp4_size = os.path.getsize(mp4_path)
            if mp4_size > 50000:
                print(f"✅ Re-encoded to MP4 H.264: {os.path.basename(mp4_path)} ({mp4_size:,} bytes)")
                return True
            else:
                print(f"❌ FFmpeg created tiny file ({mp4_size} bytes) - invalid")
                os.remove(mp4_path)
                return False
        else:
            stderr = result.stderr if result.stderr else "No error details"
            print(f"❌ FFmpeg remux failed:\n{stderr[:300]}")
            return False

    except FileNotFoundError:
        print("⚠️  FFmpeg not found. Keeping AVI format.")
        return False
    except subprocess.TimeoutExpired:
        print("⚠️  FFmpeg conversion timed out")
        return False
    except Exception as e:
        print(f"❌ Conversion error: {str(e)}")
        return False
