"""Video processing service — YOLOv8 pothole detection pipeline."""

import os
import cv2
import uuid
import numpy as np
from datetime import datetime, timezone


def process_video(video_id, config):
    """
    Process an uploaded video:
    1. Extract frames
    2. Run YOLOv8 inference on each frame
    3. Draw bounding boxes on detections
    4. Reassemble annotated video
    5. Save detection records to database
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

        # Process video
        input_path = os.path.join(config['UPLOAD_FOLDER'], video.filename)
        processed_filename = f"processed_{video.filename}"
        output_path = os.path.join(config['PROCESSED_FOLDER'], processed_filename)
        snapshots_dir = config['SNAPSHOTS_FOLDER']

        detections = _run_detection_pipeline(
            model, input_path, output_path, snapshots_dir,
            video_id, video, db
        )

        # Update video record
        video.status = 'completed'
        video.processing_progress = 100
        video.processed_filename = processed_filename
        video.processed_date = datetime.now(timezone.utc)
        video.total_detections = len(detections)
        db.session.commit()

        print(f"✅ Processing complete: {len(detections)} potholes detected")

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


def _run_detection_pipeline(model, input_path, output_path, snapshots_dir, video_id, video, db):
    """Run frame-by-frame detection and generate annotated video."""
    from models import Detection

    cap = cv2.VideoCapture(input_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Use mp4v codec for compatibility
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    all_detections = []
    frame_number = 0
    # Process every Nth frame for speed (skip frames for efficiency)
    process_every_n = max(1, int(fps / 5))  # Process ~5 frames per second

    # Track recent detections to avoid logging duplicates in close frames
    recent_detection_frames = set()
    detection_cooldown = int(fps * 2)  # 2-second cooldown between logging same area

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_number += 1

        # Update progress periodically
        if frame_number % 30 == 0:
            progress = (frame_number / total_frames) * 100
            video.processing_progress = min(progress, 99)
            db.session.commit()

        # Run inference on selected frames
        if frame_number % process_every_n == 0:
            results = model(frame, verbose=False, conf=0.25)

            for result in results:
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])
                        class_name = model.names[cls_id].lower() if cls_id < len(model.names) else ''

                        # Check if this is a pothole-related detection
                        # For custom model: class 0 = pothole
                        # For pretrained COCO: we look for relevant classes
                        is_pothole = _is_pothole_class(class_name, cls_id, model)

                        if is_pothole and conf >= 0.3:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                            # Draw bounding box
                            _draw_detection(frame, x1, y1, x2, y2, conf)

                            # Check if we should log this detection (avoid duplicates)
                            grid_key = (int(x1 / 100), int(y1 / 100))
                            frame_key = (grid_key, frame_number // detection_cooldown)

                            if frame_key not in recent_detection_frames:
                                recent_detection_frames.add(frame_key)

                                # Save snapshot
                                timestamp = frame_number / fps
                                snapshot_name = f"snap_{video_id}_{frame_number}.jpg"
                                snapshot_path = os.path.join(snapshots_dir, snapshot_name)

                                # Draw on a copy for the snapshot
                                snap_frame = frame.copy()
                                _draw_detection(snap_frame, x1, y1, x2, y2, conf)
                                cv2.imwrite(snapshot_path, snap_frame)

                                # Save detection record
                                detection = Detection(
                                    video_id=video_id,
                                    frame_number=frame_number,
                                    timestamp=timestamp,
                                    confidence=conf,
                                    bbox_x1=float(x1),
                                    bbox_y1=float(y1),
                                    bbox_x2=float(x2),
                                    bbox_y2=float(y2),
                                    frame_snapshot=snapshot_name
                                )
                                db.session.add(detection)
                                all_detections.append(detection)

        # Write frame (with or without annotations)
        out.write(frame)

    cap.release()
    out.release()

    # Commit all detections
    db.session.commit()

    # Convert to browser-compatible format using ffmpeg if available
    _convert_to_h264(output_path)

    return all_detections


def _is_pothole_class(class_name, cls_id, model):
    """Check if detection class represents a pothole."""
    # For custom-trained model (single class: pothole)
    if len(model.names) <= 5:
        return True  # Custom model with few classes — likely all are damage types

    # For pretrained COCO model (fallback) — no direct pothole class
    # We'll detect everything to demonstrate the pipeline
    pothole_keywords = ['pothole', 'hole', 'crack', 'damage', 'd40', 'd00', 'd10', 'd20']
    return any(kw in class_name for kw in pothole_keywords)


def _draw_detection(frame, x1, y1, x2, y2, confidence):
    """Draw a styled bounding box and label on the frame."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

    # Color: orange-red gradient based on confidence
    color = (0, 69, 255)  # Orange in BGR
    if confidence > 0.7:
        color = (0, 0, 255)  # Red for high confidence
    elif confidence > 0.5:
        color = (0, 140, 255)  # Dark orange

    # Draw thick bounding box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    # Draw filled background for label
    label = f"Pothole {confidence:.0%}"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.7
    thickness = 2
    (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, thickness)

    cv2.rectangle(frame, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), color, -1)
    cv2.putText(frame, label, (x1 + 5, y1 - 5), font, font_scale, (255, 255, 255), thickness)

    # Draw corner markers for style
    corner_len = 15
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, 4)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, 4)
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, 4)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, 4)
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, 4)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, 4)
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, 4)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, 4)


def _convert_to_h264(video_path):
    """Convert video to H.264 for browser compatibility."""
    import subprocess
    try:
        temp_path = video_path + '.temp.mp4'
        result = subprocess.run([
            'ffmpeg', '-y', '-i', video_path,
            '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-movflags', '+faststart',
            temp_path
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            os.replace(temp_path, video_path)
            print("✅ Video converted to H.264 for browser compatibility")
        else:
            # Clean up temp file if conversion failed
            if os.path.exists(temp_path):
                os.remove(temp_path)
            print("⚠️  ffmpeg conversion failed, using mp4v codec (may have browser issues)")
    except FileNotFoundError:
        print("⚠️  ffmpeg not found. Install ffmpeg for best browser video compatibility.")
    except subprocess.TimeoutExpired:
        print("⚠️  ffmpeg conversion timed out")
        if os.path.exists(video_path + '.temp.mp4'):
            os.remove(video_path + '.temp.mp4')
