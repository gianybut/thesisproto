"""Video management routes — upload with GPS track support."""

import os
import uuid
import threading
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from models import db, Video, Detection

videos_bp = Blueprint('videos', __name__)

ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
ALLOWED_GPS_EXTENSIONS = {'gpx', 'csv'}


def allowed_video(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def allowed_gps(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_GPS_EXTENSIONS


def get_user_id():
    """Extract user ID from session or Authorization header."""
    from flask import session
    user_id = session.get('user_id')
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            user_id = int(auth_header.split(' ')[1])
        except (ValueError, IndexError):
            pass
    return user_id


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
    cap = cv2.VideoCapture(upload_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration = frame_count / fps if fps > 0 else 0
    cap.release()

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
    )
    db.session.add(video)
    db.session.commit()

    # Start processing in background thread
    video_id = video.id
    app = current_app._get_current_object()

    def process_async():
        with app.app_context():
            from services.video_processor import process_video
            process_video(video_id, app.config)

    thread = threading.Thread(target=process_async)
    thread.daemon = True
    thread.start()

    return jsonify({
        'message': 'Video uploaded successfully. Processing started.',
        'video': video.to_dict()
    }), 201


@videos_bp.route('', methods=['GET'])
def list_videos():
    """List all videos for the current user."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    videos = Video.query.filter_by(user_id=user_id).order_by(Video.upload_date.desc()).all()
    return jsonify({
        'videos': [v.to_dict() for v in videos]
    }), 200


@videos_bp.route('/<int:video_id>', methods=['GET'])
def get_video(video_id):
    """Get video details with detections."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = Video.query.filter_by(id=video_id, user_id=user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    detections = Detection.query.filter_by(video_id=video_id).order_by(Detection.timestamp).all()

    return jsonify({
        'video': video.to_dict(),
        'detections': [d.to_dict() for d in detections]
    }), 200


@videos_bp.route('/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video and its associated data."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = Video.query.filter_by(id=video_id, user_id=user_id).first()
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

    db.session.delete(video)
    db.session.commit()

    return jsonify({'message': 'Video deleted successfully'}), 200


@videos_bp.route('/<int:video_id>/stream', methods=['GET'])
def stream_original_video(video_id):
    """Stream the original uploaded video with range request support."""
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], video.filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Video file not found'}), 404

    return _stream_file(file_path)


@videos_bp.route('/<int:video_id>/processed', methods=['GET'])
def stream_processed_video(video_id):
    """Stream the processed video with bounding boxes and range request support."""
    video = Video.query.get(video_id)
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
