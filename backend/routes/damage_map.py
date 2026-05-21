"""Damage map API routes — geo-located detection data for interactive mapping."""

from flask import Blueprint, request, jsonify
from models import db, Video, Detection, GpsTrackPoint
from sqlalchemy import func

damage_map_bp = Blueprint('damage_map', __name__)


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


@damage_map_bp.route('/detections', methods=['GET'])
def get_map_detections():
    """Get all geo-located detections for map display with optional filters."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Build query — all detections with GPS coordinates
    query = Detection.query.filter(
        Detection.latitude.isnot(None),
        Detection.longitude.isnot(None)
    )

    # Apply filters
    damage_type = request.args.get('damage_type')
    if damage_type:
        query = query.filter(Detection.damage_type == damage_type)

    severity = request.args.get('severity')
    if severity:
        query = query.filter(Detection.severity == severity)

    status = request.args.get('status')
    if status:
        query = query.filter(Detection.inspection_status == status)

    min_confidence = request.args.get('min_confidence', type=float)
    if min_confidence:
        query = query.filter(Detection.confidence >= min_confidence)

    detections = query.order_by(Detection.created_at.desc()).all()

    return jsonify({
        'total': len(detections),
        'detections': [{
            'id': d.id,
            'latitude': d.latitude,
            'longitude': d.longitude,
            'damage_type': d.damage_type,
            'damage_label': d.damage_label,
            'severity': d.severity,
            'severity_score': d.severity_score,
            'confidence': round(d.confidence, 4),
            'inspection_status': d.inspection_status,
            'road_name': d.road_name,
            'video_id': d.video_id,
            'frame_number': d.frame_number,
            'timestamp': d.timestamp,
            'frame_snapshot': d.frame_snapshot,
            'source_type': d.source_type,
            'created_at': d.created_at.isoformat() if d.created_at else None,
        } for d in detections]
    }), 200


@damage_map_bp.route('/gps-tracks', methods=['GET'])
def get_gps_tracks():
    """Get GPS track polyline data for all surveyed roads."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Get all GPS track points grouped by video
    videos_with_gps = Video.query.filter(
        Video.gps_filename.isnot(None)
    ).all()

    tracks = []
    for video in videos_with_gps:
        points = GpsTrackPoint.query.filter_by(
            video_id=video.id
        ).order_by(GpsTrackPoint.timestamp).all()

        if points:
            tracks.append({
                'video_id': video.id,
                'video_name': video.original_filename,
                'road_name': video.road_name,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'points': [[p.latitude, p.longitude] for p in points],
            })

    return jsonify({'tracks': tracks}), 200


@damage_map_bp.route('/stats', methods=['GET'])
def get_map_stats():
    """Get geographic summary statistics for the map."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Total geo-located detections
    total_geolocated = Detection.query.filter(
        Detection.latitude.isnot(None)
    ).count()

    # Detections by severity
    severity_counts = db.session.query(
        Detection.severity, func.count(Detection.id)
    ).filter(
        Detection.latitude.isnot(None),
        Detection.severity.isnot(None)
    ).group_by(Detection.severity).all()

    # Detections by damage type
    type_counts = db.session.query(
        Detection.damage_type, Detection.damage_label, func.count(Detection.id)
    ).filter(
        Detection.latitude.isnot(None)
    ).group_by(Detection.damage_type, Detection.damage_label).all()

    # Detections by status
    status_counts = db.session.query(
        Detection.inspection_status, func.count(Detection.id)
    ).filter(
        Detection.latitude.isnot(None)
    ).group_by(Detection.inspection_status).all()

    return jsonify({
        'total_geolocated': total_geolocated,
        'by_severity': {s: c for s, c in severity_counts if s},
        'by_damage_type': {t: {'label': l, 'count': c} for t, l, c in type_counts},
        'by_status': {s: c for s, c in status_counts if s},
    }), 200
