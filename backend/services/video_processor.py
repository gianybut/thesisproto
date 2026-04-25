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

        detections, actual_filename = _run_detection_pipeline(
            model, input_path, output_path, snapshots_dir,
            video_id, video, db
        )

        if actual_filename is None:
            raise Exception("Failed to create video file")

        # Update video record with actual processed filename (may differ due to codec)
        video.status = 'completed'
        video.processing_progress = 100
        video.processed_filename = actual_filename
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

    # Ensure dimensions are even (required by most video codecs)
    width = width - (width % 2)
    height = height - (height % 2)

    print(f"📹 Video info: {width}x{height} @ {fps} fps, {total_frames} frames")

    # Try multiple codecs in order of OpenCV reliability on Windows
    # MJPEG is most stable with OpenCV, AVI container most compatible with browsers
    codec_options = [
        ('MJPG', '.avi', 'Motion JPEG AVI'),     # Most stable with OpenCV
        ('XVID', '.avi', 'XVID AVI'),            # MPEG-4 in AVI container
        ('DIVX', '.avi', 'DIVX AVI'),            # Another MPEG-4 variant
        ('FFV1', '.avi', 'FFV1 AVI'),            # Lossless codec
        ('I420', '.avi', 'Uncompressed I420'),   # Fallback: uncompressed
    ]

    out = None
    output_filename = None

    for codec_name, ext, description in codec_options:
        try:
            fourcc = cv2.VideoWriter_fourcc(*codec_name)
            test_output = output_path.replace('.mp4', ext)
            test_writer = cv2.VideoWriter(test_output, fourcc, fps, (width, height))
            
            if test_writer.isOpened():
                out = test_writer
                output_filename = test_output
                print(f"✅ Using codec: {description} ({codec_name})")
                break
            else:
                test_writer.release()
        except Exception as e:
            print(f"⚠️  Codec {codec_name} failed: {str(e)}")
            continue

    if out is None or output_filename is None:
        print(f"❌ Failed to initialize video writer with ANY codec")
        print(f"   Video dimensions: {width}x{height}, FPS: {fps}")
        cap.release()
        return [], None

    all_detections = []
    frame_number = 0
    # Process every Nth frame for speed (skip frames for efficiency)
    process_every_n = max(1, int(fps / 5))  # Process ~5 frames per second

    # Track recent detections to avoid logging duplicates in close frames
    recent_detection_frames = set()
    detection_cooldown = int(fps * 2)  # 2-second cooldown between logging same area
    
    # Track active bounding boxes to draw on multiple frames
    active_boxes = {}  # {detection_id: {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'conf': conf, 'end_frame': end_frame}}
    box_persistence = int(fps * 0.5)  # Show bounding box for 0.5 seconds (15 frames at 30fps)

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

        # Remove expired bounding boxes
        expired_ids = [bid for bid, box_info in active_boxes.items() if frame_number > box_info['end_frame']]
        for bid in expired_ids:
            del active_boxes[bid]

        # Run inference on selected frames
        if frame_number % process_every_n == 0:
            # Clear previous active boxes to prevent cross-frame overlapping boxes
            active_boxes.clear()
            
            # Use appropriate confidence and NMS IoU threshold to avoid duplicates
            results = model(frame, verbose=False, conf=0.08, iou=0.40)

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

                        if is_pothole:
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                            # Store bounding box to draw on multiple frames
                            box_id = f"{frame_number}_{int(x1)}_{int(y1)}"
                            active_boxes[box_id] = {
                                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 
                                'conf': conf, 
                                'end_frame': frame_number + box_persistence
                            }

                            # Check if we should log this detection (avoid duplicates)
                            grid_key = (int(x1 / 100), int(y1 / 100))
                            frame_key = (grid_key, frame_number // detection_cooldown)

                            if frame_key not in recent_detection_frames:
                                recent_detection_frames.add(frame_key)

                                # Calculate precise timestamp (frame_number / fps gives exact seconds)
                                timestamp = float(frame_number) / float(fps)
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

        # Draw all active bounding boxes on current frame
        for box_info in active_boxes.values():
            _draw_detection(frame, box_info['x1'], box_info['y1'], box_info['x2'], box_info['y2'], box_info['conf'])

        # Write frame (with or without annotations)
        out.write(frame)

    cap.release()
    out.release()

    # Ensure the file is written to disk by checking it exists and has size
    import time
    max_wait = 5  # Wait up to 5 seconds for file to be written
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

    # Try to convert AVI to MP4 using FFmpeg for better browser compatibility
    # Only delete AVI if conversion is successful; otherwise keep AVI
    avi_path = output_filename
    mp4_path = output_filename.replace('.avi', '.mp4')
    
    conversion_success = _convert_avi_to_mp4(avi_path, mp4_path)
    if conversion_success:
        # FFmpeg conversion succeeded, use MP4 file
        try:
            os.remove(avi_path)  # Delete intermediate AVI
            output_filename = mp4_path
            print(f"✅ Using converted MP4: {os.path.basename(output_filename)}")
        except Exception as e:
            print(f"⚠️  Could not delete AVI ({e}), keeping both files")
    else:
        # FFmpeg conversion failed or skipped, use AVI
        print(f"📹 Using AVI format: {os.path.basename(output_filename)}")

    # Commit all detections
    db.session.commit()

    # Extract just the filename (not full path) for database storage
    actual_filename = os.path.basename(output_filename)
    print(f"📹 Output video: {actual_filename}")

    return all_detections, actual_filename


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


def _convert_avi_to_h264(avi_path, output_mp4_path):
    """Convert AVI video to MP4 H.264 for browser compatibility."""
    import subprocess
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-i', avi_path,
            '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '23', '-movflags', '+faststart',
            output_mp4_path
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            os.remove(avi_path)  # Remove the AVI after successful conversion
            print("✅ Video converted from AVI to H.264 MP4")
        else:
            print("⚠️  ffmpeg conversion failed, using AVI format")
    except FileNotFoundError:
        print("⚠️  ffmpeg not found. AVI video created successfully (browser playback may vary)")
    except subprocess.TimeoutExpired:
        print("⚠️  ffmpeg conversion timed out, using AVI format")
    except Exception as e:
        print(f"⚠️  Conversion error: {str(e)}")


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
            print("⚠️  ffmpeg conversion failed, using existing codec")
    except FileNotFoundError:
        print("⚠️  ffmpeg not found. Video created successfully (may have browser compatibility issues)")
    except subprocess.TimeoutExpired:
        print("⚠️  ffmpeg conversion timed out")
        if os.path.exists(video_path + '.temp.mp4'):
            os.remove(video_path + '.temp.mp4')
    except Exception as e:
        print(f"⚠️  Conversion error: {str(e)}")


def _convert_avi_to_mp4(avi_path, mp4_path):
    """Convert AVI video to MP4 container using H.264 encoding for browser compatibility."""
    import subprocess
    try:
        print(f"🔄 Re-encoding AVI to MP4 H.264 for browser compatibility...")
        
        # Use libx264 for web compatibility
        result = subprocess.run([
            'ffmpeg', '-y', '-i', avi_path,
            '-c:v', 'libx264', '-preset', 'fast',
            '-crf', '28',     # Good balance of size/quality
            '-c:a', 'aac',    # Encode audio to AAC
            '-movflags', '+faststart',
            mp4_path
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0 and os.path.exists(mp4_path):
            mp4_size = os.path.getsize(mp4_path)
            if mp4_size > 50000:  # At least 50KB (valid video)
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
