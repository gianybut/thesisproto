"""Detection and dashboard statistics routes."""

from flask import Blueprint, request, jsonify
from models import db, Video, Detection
from sqlalchemy import func

detections_bp = Blueprint('detections', __name__)


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


@detections_bp.route('/detections/<int:video_id>', methods=['GET'])
def get_detections(video_id):
    """Get all detections for a specific video."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = Video.query.filter_by(id=video_id, user_id=user_id).first()
    if not video:
        return jsonify({'error': 'Video not found'}), 404

    detections = Detection.query.filter_by(video_id=video_id).order_by(Detection.timestamp).all()

    return jsonify({
        'video_id': video_id,
        'total_detections': len(detections),
        'detections': [d.to_dict() for d in detections]
    }), 200


@detections_bp.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get aggregate dashboard statistics."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Total videos
    total_videos = Video.query.filter_by(user_id=user_id).count()

    # Videos by status
    completed_videos = Video.query.filter_by(user_id=user_id, status='completed').count()
    processing_videos = Video.query.filter_by(user_id=user_id, status='processing').count()

    # Total detections
    total_detections = db.session.query(func.sum(Video.total_detections)).filter(
        Video.user_id == user_id
    ).scalar() or 0

    # Average confidence
    avg_confidence = db.session.query(func.avg(Detection.confidence)).join(Video).filter(
        Video.user_id == user_id
    ).scalar() or 0

    # Total video duration processed
    total_duration = db.session.query(func.sum(Video.duration)).filter(
        Video.user_id == user_id,
        Video.status == 'completed'
    ).scalar() or 0

    # Recent detections
    recent_detections = Detection.query.join(Video).filter(
        Video.user_id == user_id
    ).order_by(Detection.created_at.desc()).limit(10).all()

    # Recent videos
    recent_videos = Video.query.filter_by(user_id=user_id).order_by(
        Video.upload_date.desc()
    ).limit(5).all()

    return jsonify({
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'processing_videos': processing_videos,
        'total_detections': int(total_detections),
        'avg_confidence': round(float(avg_confidence), 4),
        'total_duration': round(float(total_duration), 1),
        'recent_detections': [d.to_dict() for d in recent_detections],
        'recent_videos': [v.to_dict() for v in recent_videos]
    }), 200
