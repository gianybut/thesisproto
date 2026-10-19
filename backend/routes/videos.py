"""Video management routes — upload with GPS track support."""

import os
import io
import csv
import json
import uuid
import threading
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app, send_file, Response
from werkzeug.utils import secure_filename
from models import db, Video, Detection, GpsTrackPoint, RouteControlPoint
from auth_tokens import current_user_id as get_user_id, visible_videos
from services.activity import record

videos_bp = Blueprint('videos', __name__)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
ALLOWED_GPS_EXTENSIONS = {'gpx', 'csv'}


def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_gps(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_GPS_EXTENSIONS


@videos_bp.route('/upload', methods=['POST'])
def upload_video():
    """Upload a road survey video with optional GPS track file for processing."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_video(file.filename):
        return jsonify({'error': f'File type not allowed. Supported: {", ".join(ALLOWED_VIDEO_EXTENSIONS)}'}), 400

    # Generate unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    # Save the video file
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(upload_path)

    # Get video metadata using OpenCV
    import cv2
    from services.video_processor import open_upright
    cap, _rotate, width, height = open_upright(upload_path)   # width x height as displayed
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

    # Enforce the length limit in code, not just in the paper (thesis Sec 1.7 / 3.4)
    max_s = current_app.config.get('MAX_VIDEO_DURATION_S', 600)
    if duration > max_s:
        os.remove(upload_path)
        return jsonify({
            'error': (f'This video is {duration / 60:.1f} minutes long. Videos must be '
                      f'{max_s // 60} minutes or shorter — trim it and upload again.')
        }), 400

    # Handle GPS track file (optional)
    gps_filename = None
    gps_original_filename = None

    if 'gps_file' in request.files:
        gps_file = request.files['gps_file']
        if gps_file.filename and gps_file.filename != '':
            if not allowed_gps(gps_file.filename):
                return jsonify({'error': f'GPS file type not allowed. Supported: {", ".join(ALLOWED_GPS_EXTENSIONS)}'}), 400

            gps_original_filename = secure_filename(gps_file.filename)
            gps_ext = gps_original_filename.rsplit('.', 1)[1].lower()
            gps_filename = f"{uuid.uuid4().hex}.{gps_ext}"
            gps_path = os.path.join(current_app.config['UPLOAD_FOLDER'], gps_filename)
            gps_file.save(gps_path)

    # Get optional parameters
    time_offset = float(request.form.get('time_offset', 0))
    road_name = request.form.get('road_name', None)

    # Create database record
    video = Video(
        filename=unique_filename,
        original_filename=original_filename,
        file_size=os.path.getsize(upload_path),
        duration=duration,
        fps=fps,
        resolution=f"{width}x{height}",
        status='uploaded',
        user_id=user_id,
        gps_filename=gps_filename,
        gps_original_filename=gps_original_filename,
        time_offset=time_offset,
        road_name=road_name,
        position_source='gps_file' if gps_filename else 'none',
    )
    db.session.add(video)
    db.session.commit()
    record('survey_uploaded',
           f'Uploaded "{video.name}" ({duration / 60:.1f} min, {"with" if gps_filename else "without"} a GPS track)',
           target_type='survey', target_id=video.id)

    _start_processing(video.id)

    return jsonify({
        'message': 'Video uploaded successfully. Processing started.',
        'video': video.to_dict()
    }), 201


def _start_processing(video_id):
    """Run the analysis in a background thread (it dies with the server; see create_app)."""
    app = current_app._get_current_object()

    def process_async():
        with app.app_context():
            from services.video_processor import process_video
            process_video(video_id, app.config)

    thread = threading.Thread(target=process_async)
    thread.daemon = True
    thread.start()


@videos_bp.route('/<int:video_id>/reprocess', methods=['POST'])
def reprocess_video(video_id):
    """Analyse a survey again from the files already on the server, so nobody has to upload the
    video a second time: after a failure (for example the model was missing), or to test a
    changed model or setting on a finished survey. Its damage records are replaced, including any
    inspection status set on them; the clients ask for confirmation first."""
    from services.video_processor import model_file_problem

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    if video.status not in ('failed', 'completed'):
        return jsonify({'error': 'This survey is still being analysed. Wait for it to finish.'}), 409
    if not os.path.exists(os.path.join(current_app.config['UPLOAD_FOLDER'], video.filename)):
        return jsonify({'error': 'The video file is no longer on the server. Upload the survey again.'}), 410
    problem = model_file_problem(current_app.config['MODEL_PATH'])
    if problem:
        return jsonify({'error': problem}), 503

    replaced = video.total_detections or 0
    # Clear what a partial run may have left; the GPS track is read again from its file.
    for d in video.detections:
        if d.frame_snapshot:
            snap = os.path.join(current_app.config['SNAPSHOTS_FOLDER'], d.frame_snapshot)
            if os.path.exists(snap):
                os.remove(snap)
    Detection.query.filter_by(video_id=video.id).delete()
    GpsTrackPoint.query.filter_by(video_id=video.id).delete()
    video.status = 'uploaded'
    video.processing_progress = 0
    video.total_detections = 0
    video.error_message = None
    db.session.commit()
    record('survey_reanalysed', f'Started the analysis of "{video.name}" again'
           + (f', replacing {replaced} damage records' if replaced else ''), target_type='survey', target_id=video.id)

    _start_processing(video.id)
    return jsonify({'message': 'Analysing the survey again.', 'video': video.to_dict()}), 202


@videos_bp.route('/export', methods=['GET'])
def export_videos():
    """Per-video processing statistics — the throughput data for the evaluation chapter.

    ?format=csv (default) or json. One row per video the caller can see (all for an admin):
      frames            = duration × fps
      sampled_frames    = frames actually run through the model (every fps/INFERENCE_FPS-th)
      processing_seconds= wall-clock from upload complete to processing complete
    """
    from services.video_processor import INFERENCE_FPS

    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    videos = visible_videos().order_by(Video.upload_date).all()
    rows = []
    for v in videos:
        fps = v.fps or 0
        frames = round((v.duration or 0) * fps)
        skip = max(1, int(fps / INFERENCE_FPS)) if fps else 1
        processing = None
        if v.processed_date and v.upload_date:
            processing = round((v.processed_date - v.upload_date).total_seconds(), 1)
        rows.append({
            'id': v.id,
            'name': v.name,
            'original_filename': v.original_filename,
            'status': v.status,
            'duration_s': round(v.duration, 2) if v.duration else None,
            'fps': round(fps, 2) if fps else None,
            'frames': frames,
            'inference_fps': INFERENCE_FPS,
            'sampled_frames': frames // skip if frames else 0,
            'total_detections': v.total_detections,
            'position_source': v.position_source or 'none',
            'has_gps': v.gps_filename is not None,
            'control_point_count': len(v.control_points),
            'upload_date': v.upload_date.isoformat() if v.upload_date else None,
            'processed_date': v.processed_date.isoformat() if v.processed_date else None,
            'processing_seconds': processing,
        })

    if request.args.get('format', 'csv') == 'json':
        return Response(json.dumps(rows, indent=2), mimetype='application/json',
                        headers={'Content-Disposition': 'attachment;filename=video_processing_stats.json'})

    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return Response(output.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition': 'attachment;filename=video_processing_stats.csv'})


@videos_bp.route('', methods=['GET'])
def list_videos():
    """List the surveys the caller can see: their own, or every survey for an admin."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    videos = visible_videos().order_by(Video.upload_date.desc()).all()
    return jsonify({
        'videos': [v.to_dict() for v in videos]
    }), 200


@videos_bp.route('/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Get video details with detections."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    detections = Detection.query.filter_by(video_id=video_id).order_by(Detection.timestamp).all()

    return jsonify({
        'video': video.to_dict(),
        'detections': [d.to_dict() for d in detections]
    }), 200


@videos_bp.route('/<int:video_id>', methods=['PATCH'])
def rename_video(video_id):
    """Rename a video. Body: {"name": "Rizal Ave northbound"}.

    Stores a display_name; the uploaded filename is never overwritten. Sending an
    empty name clears the label and falls back to the original filename.
    """
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'name' not in data:
        return jsonify({'error': 'Body must be {"name": "..."}'}), 400

    name = (data.get('name') or '').strip()
    if len(name) > 300:
        return jsonify({'error': 'Name must be 300 characters or fewer'}), 400

    old_name = video.name
    video.display_name = name or None
    db.session.commit()
    record('survey_renamed', f'Renamed "{old_name}" to "{video.name}"', target_type='survey', target_id=video.id)

    return jsonify({'message': 'Video renamed', 'video': video.to_dict()}), 200


@videos_bp.route('/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video and its associated data."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Delete files
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.filename)
    if os.path.exists(upload_path):
        os.remove(upload_path)

    if video.gps_filename:
        gps_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.gps_filename)
        if os.path.exists(gps_path):
            os.remove(gps_path)

    if video.processed_filename:
        processed_path = os.path.join(current_app.config['PROCESSED_FOLDER'], video.processed_filename)
        if os.path.exists(processed_path):
            os.remove(processed_path)

    # Delete snapshots
    for detection in video.detections:
        if detection.frame_snapshot:
            snap_path = os.path.join(current_app.config['SNAPSHOTS_FOLDER'], detection.frame_snapshot)
            if os.path.exists(snap_path):
                os.remove(snap_path)

    summary = f'Deleted "{video.name}" and its {video.total_detections or 0} damage records'
    if video.user_id != user_id:
        summary += f' (uploaded by {video.uploader.username if video.uploader else "a removed account"})'
    db.session.delete(video)
    db.session.commit()
    record('survey_deleted', summary, target_type='survey', target_id=video_id)

    return jsonify({'message': 'Video deleted successfully'}), 200


@videos_bp.route('/<int:video_id>/stream', methods=['GET'])
def stream_original_video(video_id):
    """Stream the original uploaded video with range request support."""
    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video file not found'}), 404

    return _stream_file(file_path)


@videos_bp.route('/<int:video_id>/processed', methods=['GET'])
def stream_processed_video(video_id):
    """Stream the processed video with bounding boxes and range request support."""
    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    if not video.processed_filename:
        return jsonify({'error': 'Video has not been processed yet'}), 404

    file_path = os.path.join(current_app.config['PROCESSED_FOLDER'], video.processed_filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Processed video file not found'}), 404

    return _stream_file(file_path)


@videos_bp.route('/<int:video_id>/snapshot/<path:filename>', methods=['GET'])
def get_snapshot(video_id, filename):
    """Serve a detection snapshot image."""
    file_path = os.path.join(current_app.config['SNAPSHOTS_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Snapshot not found'}), 404

    return send_file(file_path, mimetype='image/jpeg')


# ---------------------------------------------------------------------------
# Control-point georeferencing — fallback for videos uploaded without a GPS track
# ---------------------------------------------------------------------------

def _control_points_payload(video, applied=None, message=None):
    """Common response body for the control-point endpoints."""
    body = {
        'control_points': [cp.to_dict() for cp in video.control_points],
        'position_source': video.position_source,
        'video': video.to_dict(),
    }
    if applied is not None:
        body['applied'] = applied
    if message:
        body['message'] = message
    return body


@videos_bp.route('/<int:video_id>/control-points', methods=['GET'])
def get_control_points(video_id):
    """List the control points saved for a video."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    return jsonify(_control_points_payload(video)), 200


@videos_bp.route('/<int:video_id>/control-points', methods=['POST'])
def save_control_points(video_id):
    """Replace a video's control points and re-georeference its existing detections.

    Body: {"control_points": [{"video_time_s": 12.5, "latitude": 14.6, "longitude": 121.0}, ...]}
    Points must be in strictly increasing video_time_s order and inside the Philippines.
    """
    from services.georeference_service import validate_control_points, apply_control_points_to_detections

    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    if video.gps_filename:
        return jsonify({'error': 'Video already has a GPS track — manual georeferencing is only for videos without one'}), 409
    if video.status in ('uploaded', 'processing'):
        return jsonify({'error': 'Video is still processing. Wait for it to finish before saving control points'}), 409

    data = request.get_json(silent=True) or {}
    points = data.get('control_points')
    if not isinstance(points, list):
        return jsonify({'error': 'Body must be {"control_points": [...]}'}), 400

    valid, message = validate_control_points(points, max_time_s=video.duration)
    if not valid:
        return jsonify({'error': message}), 400

    # Replace semantics — the client always sends the full set
    RouteControlPoint.query.filter_by(video_id=video.id).delete()
    for seq, p in enumerate(points):
        db.session.add(RouteControlPoint(
            video_id=video.id,
            seq=seq,
            video_time_s=float(p['video_time_s']),
            latitude=float(p['latitude']),
            longitude=float(p['longitude']),
        ))
    db.session.commit()
    db.session.refresh(video)

    applied = apply_control_points_to_detections(video, db)
    record('survey_placed', f'Placed "{video.name}" on the map with {len(points)} points '
           f'({applied["positioned"]} damage records positioned)', target_type='survey', target_id=video.id)

    return jsonify(_control_points_payload(
        video, applied,
        f"Saved {len(points)} control points; positioned {applied['positioned']} of "
        f"{applied['positioned'] + applied['unpositioned']} detections"
    )), 200


@videos_bp.route('/<int:video_id>/control-points/<int:cp_id>', methods=['DELETE'])
def delete_control_point(video_id, cp_id):
    """Remove one control point and re-georeference; with fewer than 2 left all positions are cleared."""
    from services.georeference_service import apply_control_points_to_detections

    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    if video.status in ('uploaded', 'processing'):
        return jsonify({'error': 'Video is still processing. Wait for it to finish before changing control points'}), 409

    cp = RouteControlPoint.query.filter_by(id=cp_id, video_id=video.id).first()
    if not cp:
        return jsonify({'error': 'Control point not found'}), 404

    db.session.delete(cp)
    db.session.flush()
    remaining = RouteControlPoint.query.filter_by(video_id=video.id).order_by(RouteControlPoint.video_time_s).all()
    for seq, point in enumerate(remaining):
        point.seq = seq
    db.session.commit()
    db.session.refresh(video)

    applied = apply_control_points_to_detections(video, db)

    return jsonify(_control_points_payload(video, applied, 'Control point deleted')), 200


def _stream_file(file_path):
    """Stream a file with proper range request support for all browsers (Safari, Chrome, Firefox)."""
    from flask import Response

    ext = os.path.splitext(file_path)[1].lower()
    mime_type_map = {
        '.mp4': 'video/mp4', '.avi': 'video/x-msvideo',
        '.mov': 'video/quicktime', '.mkv': 'video/x-matroska',
        '.webm': 'video/webm'
    }
    mime_type = mime_type_map.get(ext, 'video/mp4')

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range')

    if range_header:
        try:
            # Parse "bytes=start-end" format — handle cases like "bytes=0-" or "bytes=0-1"
            range_str = range_header.replace('bytes=', '').strip()
            parts = range_str.split('-')
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

            # Clamp values to valid range
            start = max(0, min(start, file_size - 1))
            end = max(start, min(end, file_size - 1))
            chunk_size = end - start + 1

        except (ValueError, IndexError):
            # Malformed range header — return full file
            return send_file(file_path, mimetype=mime_type)

        def generate():
            with open(file_path, 'rb') as f:
                f.seek(start)
                remaining = chunk_size
                while remaining > 0:
                    read_size = min(8192, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        response = Response(generate(), status=206, mimetype=mime_type)
        response.headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'
        response.headers['Content-Length'] = chunk_size
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        return response
    else:
        response = send_file(file_path, mimetype=mime_type)
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Content-Length'] = file_size
        return response
