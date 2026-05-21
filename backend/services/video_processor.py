"""Video processing service — YOLOv8 road damage detection pipeline with GPS sync and severity."""

import os
import cv2
import uuid
import numpy as np
from datetime import datetime, timezone


# Damage class label mapping (RDD2022 standard)
DAMAGE_CLASS_MAP = {
    'd00': ('D00', 'Linear Crack'),
    'd10': ('D10', 'Longitudinal Crack'),
    'd20': ('D20', 'Transverse Crack'),
    'd30': ('D30', 'Alligator Crack'),
    'd40': ('D40', 'Pothole'),
    'pothole': ('D40', 'Pothole'),
    'longitudinal': ('D10', 'Longitudinal Crack'),
    'transverse': ('D20', 'Transverse Crack'),
    'alligator': ('D30', 'Alligator Crack'),
}

# Colors for each damage type (BGR format for OpenCV)
DAMAGE_COLORS = {
    'D10': (255, 165, 0),    # Orange — Longitudinal
    'D20': (0, 255, 255),    # Yellow — Transverse
    'D30': (0, 0, 255),      # Red — Alligator
    'D40': (0, 69, 255),     # Dark Orange — Pothole
}


def process_video(video_id, config):
    """
    Process an uploaded video:
    1. Extract frames
    2. Run YOLOv8 inference on each frame
    3. Assign GPS coordinates via timestamp synchronization
    4. Calculate severity scores
    5. Draw bounding boxes on detections
    6. Reassemble annotated video
    7. Save detection records to database
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
    db.session.commit()

    try:
        # Load YOLOv8 model
        model = _load_model(config['MODEL_PATH'])

        # Load GPS track if available
        gps_points = _load_gps_track(video, config)

        # Process video
        input_path = os.path.join(config['UPLOAD_FOLDER'], video.filename)
        processed_filename = f"processed_{video.filename}"
        output_path = os.path.join(config['PROCESSED_FOLDER'], processed_filename)
        snapshots_dir = config['SNAPSHOTS_FOLDER']

        detections, actual_filename = _run_detection_pipeline(
            model, input_path, output_path, snapshots_dir,
            video_id, video, db, gps_points
        )

        if actual_filename is None:
            raise Exception("Failed to create video file")

        # Calculate severity scores after all detections are collected
        _calculate_batch_severity(detections, video, db)

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
        db.session.commit()


def _load_model(model_path):
    """Load YOLOv8 model, falling back to pretrained if custom model not found."""
    from ultralytics import YOLO

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
        # Try to map by class index for RDD2022-style models
        rdd_map = {0: ('D00', 'Linear Crack'), 1: ('D10', 'Longitudinal Crack'),
                   2: ('D20', 'Transverse Crack'), 3: ('D30', 'Alligator Crack'),
                   4: ('D40', 'Pothole')}
        if cls_id in rdd_map:
            return rdd_map[cls_id][0], rdd_map[cls_id][1], True
        return 'D40', 'Pothole', True  # Default to pothole for single-class models

    # For pretrained COCO model (fallback) — no direct damage classes
    return 'D40', 'Pothole', False


def _run_detection_pipeline(model, input_path, output_path, snapshots_dir, video_id, video, db, gps_points=None):
    """Run frame-by-frame detection and generate annotated video."""
    from models import Detection
    from services.gps_service import interpolate_gps

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Ensure dimensions are even (required by most video codecs)
    width = width - (width % 2)
    height = height - (height % 2)

    print(f"📹 Video info: {width}x{height} @ {fps} fps, {total_frames} frames")

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
    process_every_n = max(1, int(fps / 5))  # Process ~5 frames per second

    recent_detection_frames = set()
    detection_cooldown = int(fps * 2)

    active_boxes = {}
    box_persistence = int(fps * 0.5)

    time_offset = video.time_offset or 0.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

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

            results = model(frame, verbose=False, conf=0.15, iou=0.45)

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

                            grid_key = (int(x1 / 100), int(y1 / 100))
                            frame_key = (grid_key, frame_number // detection_cooldown)

                            if frame_key not in recent_detection_frames:
                                recent_detection_frames.add(frame_key)

                                # Formula 18: t_frame = frame_number / FPS
                                timestamp = float(frame_number) / float(fps)

                                # GPS Synchronization (Formula 19)
                                latitude = None
                                longitude = None
                                if gps_points:
                                    gps_coord = interpolate_gps(gps_points, timestamp, time_offset)
                                    if gps_coord:
                                        latitude = gps_coord['latitude']
                                        longitude = gps_coord['longitude']

                                snapshot_name = f"snap_{video_id}_{frame_number}.jpg"
                                snapshot_path = os.path.join(snapshots_dir, snapshot_name)

                                snap_frame = frame.copy()
                                _draw_detection(snap_frame, x1, y1, x2, y2, conf,
                                                damage_code, damage_label, damage_color)
                                cv2.imwrite(snapshot_path, snap_frame)

                                detection = Detection(
                                    video_id=video_id,
                                    frame_number=frame_number,
                                    timestamp=timestamp,
                                    confidence=conf,
                                    bbox_x1=float(x1),
                                    bbox_y1=float(y1),
                                    bbox_x2=float(x2),
                                    bbox_y2=float(y2),
                                    frame_snapshot=snapshot_name,
                                    damage_type=damage_code,
                                    damage_label=damage_label,
                                    latitude=latitude,
                                    longitude=longitude,
                                    road_name=video.road_name,
                                    source_type='ai_detection',
                                )
                                db.session.add(detection)
                                all_detections.append(detection)

        for box_info in active_boxes.values():
            _draw_detection(frame, box_info['x1'], box_info['y1'],
                            box_info['x2'], box_info['y2'], box_info['conf'],
                            box_info.get('damage_code', 'D40'),
                            box_info.get('damage_label', 'Pothole'),
                            box_info.get('color', (0, 69, 255)))

        # Write frame to output
        out.write(frame)

    cap.release()

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


def _calculate_batch_severity(detections, video, db):
    """Calculate severity scores for all detections using cluster analysis."""
    if not detections:
        return

    from services.severity_service import calculate_severity

    # Build list of detection dicts for cluster analysis
    det_dicts = []
    for d in detections:
        det_dicts.append({
            'damage_type': d.damage_type,
            'confidence': d.confidence,
            'bbox_x1': d.bbox_x1,
            'bbox_y1': d.bbox_y1,
            'bbox_x2': d.bbox_x2,
            'bbox_y2': d.bbox_y2,
            'latitude': d.latitude,
            'longitude': d.longitude,
        })

    # Parse resolution for frame dimensions
    frame_w, frame_h = 640, 640
    if video.resolution:
        try:
            parts = video.resolution.split('x')
            frame_w, frame_h = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass

    # Calculate severity for each detection
    for i, detection in enumerate(detections):
        result = calculate_severity(det_dicts[i], all_detections=det_dicts,
                                     frame_width=frame_w, frame_height=frame_h)
        detection.severity_score = result['score']
        detection.severity = result['level']

    db.session.commit()
    print(f"📊 Severity scores calculated for {len(detections)} detections")


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

    pothole_keywords = ['pothole', 'hole', 'crack', 'damage', 'd40', 'd00', 'd10', 'd20']
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
