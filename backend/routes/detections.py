"""Detection and dashboard statistics routes — with damage type and status breakdowns."""

from flask import Blueprint, request, jsonify
from models import db, Video, Detection, PublicReport
from auth_tokens import current_user_id as get_user_id, is_admin, video_scope, visible_videos
from sqlalchemy import func

detections_bp = Blueprint('detections', __name__)


@detections_bp.route('/detections/<int:video_id>', methods=['GET'])
def get_detections(video_id):
    """Get all detections for a specific video."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video = visible_videos().filter_by(id=video_id).first()
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
    """Overview statistics over the surveys the caller can see (every survey for an admin)."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    scope = video_scope()

    # Total videos
    total_videos = Video.query.filter(scope).count()

    # Videos by status
    completed_videos = Video.query.filter(scope, Video.status == 'completed').count()
    processing_videos = Video.query.filter(scope, Video.status == 'processing').count()

    # Total detections
    total_detections = db.session.query(func.sum(Video.total_detections)).filter(
        scope
    ).scalar() or 0

    # Average confidence
    avg_confidence = db.session.query(func.avg(Detection.confidence)).join(Video).filter(
        scope
    ).scalar() or 0

    # Total video duration processed
    total_duration = db.session.query(func.sum(Video.duration)).filter(
        scope,
        Video.status == 'completed'
    ).scalar() or 0

    # Damage type breakdown
    type_counts = db.session.query(
        Detection.damage_type, Detection.damage_label, func.count(Detection.id)
    ).join(Video).filter(
        scope
    ).group_by(Detection.damage_type, Detection.damage_label).all()

    # Status breakdown
    status_counts = db.session.query(
        Detection.inspection_status, func.count(Detection.id)
    ).join(Video).filter(
        scope
    ).group_by(Detection.inspection_status).all()

    # Geo-located count
    geolocated_count = Detection.query.join(Video).filter(
        scope,
        Detection.latitude.isnot(None)
    ).count()

    # Pending public reports
    pending_reports = PublicReport.query.filter_by(status='pending').count()

    # Recent detections
    recent_detections = Detection.query.join(Video).filter(
        scope
    ).order_by(Detection.created_at.desc()).limit(10).all()

    # Recent videos
    recent_videos = Video.query.filter(scope).order_by(
        Video.upload_date.desc()
    ).limit(5).all()

    return jsonify({
        'scope': 'all' if is_admin() else 'own',
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'processing_videos': processing_videos,
        'total_detections': int(total_detections),
        'avg_confidence': round(float(avg_confidence), 4),
        'total_duration': round(float(total_duration), 1),
        'by_damage_type': [{'type': t, 'label': l, 'count': c} for t, l, c in type_counts],
        'by_status': {s: c for s, c in status_counts if s},
        'geolocated_count': geolocated_count,
        'pending_reports': pending_reports,
        'recent_detections': [d.to_dict() for d in recent_detections],
        'recent_videos': [v.to_dict() for v in recent_videos]
    }), 200
