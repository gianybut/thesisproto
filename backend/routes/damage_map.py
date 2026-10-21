"""Damage map API routes — geo-located detection data for interactive mapping."""

from flask import Blueprint, request, jsonify
from models import db, Video, Detection, GpsTrackPoint
from auth_tokens import can_open_video, current_user_id as get_user_id
from sqlalchemy import func

damage_map_bp = Blueprint('damage_map', __name__)


@damage_map_bp.route('/videos', methods=['GET'])
def get_mappable_videos():
    """List videos that have at least one positioned detection, for the map switcher."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    rows = db.session.query(
        Video.id, Video.display_name, Video.original_filename, Video.road_name,
        Video.position_source, Video.user_id, func.count(Detection.id)
    ).join(Detection, Detection.video_id == Video.id).filter(
        Detection.latitude.isnot(None)
    ).group_by(Video.id).order_by(Video.upload_date.desc()).all()

    return jsonify({
        'videos': [{
            'id': vid,
            'name': display or original,
            'road_name': road,
            'position_source': source,
            'detection_count': count,
            'can_open': can_open_video(owner),  # the map is shared; opening the survey is not
        } for vid, display, original, road, source, owner, count in rows]
    }), 200


@damage_map_bp.route('/detections', methods=['GET'])
def get_map_detections():
    """Get geo-located detections for map display.

    Pass ?video_id=<id> to show a single survey's map instead of every survey.
    """
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Build query — all detections with GPS coordinates
    query = Detection.query.filter(
        Detection.latitude.isnot(None),
        Detection.longitude.isnot(None)
    )

    # Restrict to one video when asked
    video_id = request.args.get('video_id', type=int)
    if video_id:
        query = query.filter(Detection.video_id == video_id)

    # Apply filters
    damage_type = request.args.get('damage_type')
    if damage_type:
        query = query.filter(Detection.damage_type == damage_type)

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
            'confidence': round(d.confidence, 4),
            'inspection_status': d.inspection_status,
            'road_name': d.road_name,
            'video_id': d.video_id,
            'frame_number': d.frame_number,
            'timestamp': d.timestamp,
            'timestamp_formatted': d._format_timestamp(),
            # The damage's box in the snapshot, so the map's preview can zoom to it.
            'bbox': {'x1': d.bbox_x1, 'y1': d.bbox_y1, 'x2': d.bbox_x2, 'y2': d.bbox_y2},
            'frame_snapshot': d.frame_snapshot,
            'source_type': d.source_type,
            'position_source': d.position_source,
            'ai_check_score': d.ai_check_score,
            'ai_flagged': d.ai_flagged,
            'created_at': d.created_at.isoformat() if d.created_at else None,
            'can_open_video': bool(d.video and can_open_video(d.video.user_id)),
        } for d in detections]
    }), 200


@damage_map_bp.route('/gps-tracks', methods=['GET'])
def get_gps_tracks():
    """Route polyline per survey, first point to last. Pass ?video_id=<id> for a single survey.

    A survey uploaded with a GPS log returns its full track (`source: gps_file`). A survey
    positioned by hand has no log, so its route is the straight segments between the control
    points the user placed (`source: control_points`) — the same path its detections were
    interpolated along.
    """
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    track_query = Video.query.filter(
        Video.gps_filename.isnot(None) | (Video.position_source == 'georeferenced')
    )

    video_id = request.args.get('video_id', type=int)
    if video_id:
        track_query = track_query.filter(Video.id == video_id)

    tracks = []
    for video in track_query.all():
        if video.gps_filename:
            source = 'gps_file'
            points = GpsTrackPoint.query.filter_by(
                video_id=video.id
            ).order_by(GpsTrackPoint.timestamp).all()
        else:
            source = 'control_points'
            points = video.control_points  # relationship is ordered by video_time_s

        if len(points) >= 2:
            tracks.append({
                'video_id': video.id,
                'video_name': video.name,
                'road_name': video.road_name,
                'source': source,
                'upload_date': video.upload_date.isoformat() if video.upload_date else None,
                'points': [[p.latitude, p.longitude] for p in points],
            })

    return jsonify({'tracks': tracks}), 200


@damage_map_bp.route('/stats', methods=['GET'])
def get_map_stats():
    """Get geographic summary statistics. Pass ?video_id=<id> for a single survey."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    video_id = request.args.get('video_id', type=int)

    def scoped(query):
        """Apply the shared 'has a position' filter, plus the video filter when set."""
        query = query.filter(Detection.latitude.isnot(None))
        if video_id:
            query = query.filter(Detection.video_id == video_id)
        return query

    # Total geo-located detections
    total_geolocated = scoped(Detection.query).count()

    # Detections by damage type
    type_counts = scoped(db.session.query(
        Detection.damage_type, Detection.damage_label, func.count(Detection.id)
    )).group_by(Detection.damage_type, Detection.damage_label).all()

    # Detections by status
    status_counts = scoped(db.session.query(
        Detection.inspection_status, func.count(Detection.id)
    )).group_by(Detection.inspection_status).all()

    return jsonify({
        'total_geolocated': total_geolocated,
        'by_damage_type': {t: {'label': l, 'count': c} for t, l, c in type_counts},
        'by_status': {s: c for s, c in status_counts if s},
    }), 200
