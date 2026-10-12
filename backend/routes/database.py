"""Centralized database routes — damage records management and export."""

import csv
import io
import json
from flask import Blueprint, request, jsonify, Response
from models import db, Video, Detection, PublicReport, DAMAGE_TYPES, INSPECTION_STATUSES
from auth_tokens import current_user_id as get_user_id
from sqlalchemy import func

database_bp = Blueprint('database', __name__)


@database_bp.route('/detections', methods=['GET'])
def get_all_detections():
    """Get all detections across all videos with filters and pagination."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    query = Detection.query

    # Filters
    damage_type = request.args.get('damage_type')
    if damage_type:
        query = query.filter(Detection.damage_type == damage_type)

    status = request.args.get('status')
    if status:
        query = query.filter(Detection.inspection_status == status)

    source = request.args.get('source')
    if source:
        query = query.filter(Detection.source_type == source)

    has_gps = request.args.get('has_gps')
    if has_gps == 'true':
        query = query.filter(Detection.latitude.isnot(None))

    search = request.args.get('search')
    if search:
        query = query.filter(
            Detection.road_name.ilike(f'%{search}%') |
            Detection.damage_label.ilike(f'%{search}%')
        )

    # Sorting
    sort_by = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')

    sort_map = {
        'created_at': Detection.created_at,
        'confidence': Detection.confidence,
        'damage_type': Detection.damage_type,
        'status': Detection.inspection_status,
    }
    sort_col = sort_map.get(sort_by, Detection.created_at)
    if sort_dir == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 200)  # Cap at 200

    total = query.count()
    detections = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
        'detections': [d.to_dict() for d in detections]
    }), 200


@database_bp.route('/detections/<int:detection_id>/status', methods=['PUT'])
def update_detection_status(detection_id):
    """Update the inspection/repair status of a detection."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    detection = Detection.query.get(detection_id)
    if not detection:
        return jsonify({'error': 'Detection not found'}), 404

    new_status = data.get('inspection_status')
    if new_status and new_status in INSPECTION_STATUSES:
        detection.inspection_status = new_status

    repair_status = data.get('repair_status')
    if repair_status is not None:
        detection.repair_status = repair_status

    road_name = data.get('road_name')
    if road_name is not None:
        detection.road_name = road_name

    db.session.commit()

    return jsonify({
        'message': 'Detection status updated.',
        'detection': detection.to_dict()
    }), 200


@database_bp.route('/export', methods=['GET'])
def export_data():
    """Export detection data as CSV or JSON."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    format_type = request.args.get('format', 'csv')

    detections = Detection.query.order_by(Detection.created_at.desc()).all()
    data = [d.to_dict() for d in detections]

    if format_type == 'json':
        return Response(
            json.dumps(data, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment;filename=road_damage_data.json'}
        )
    else:
        # CSV export
        output = io.StringIO()
        if data:
            fieldnames = ['id', 'damage_type', 'damage_label',
                          'confidence', 'latitude', 'longitude', 'position_source', 'road_name',
                          'inspection_status', 'source_type', 'created_at',
                          'video_id', 'frame_number', 'timestamp']
            writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            for row in data:
                flat_row = {k: v for k, v in row.items() if k in fieldnames}
                writer.writerow(flat_row)

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=road_damage_data.csv'}
        )


@database_bp.route('/stats', methods=['GET'])
def get_database_stats():
    """Get aggregate database statistics for the dashboard."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    # Total detections
    total = Detection.query.count()

    # By damage type
    type_counts = db.session.query(
        Detection.damage_type, Detection.damage_label, func.count(Detection.id)
    ).group_by(Detection.damage_type, Detection.damage_label).all()

    # By status
    status_counts = db.session.query(
        Detection.inspection_status, func.count(Detection.id)
    ).group_by(Detection.inspection_status).all()

    # By source
    source_counts = db.session.query(
        Detection.source_type, func.count(Detection.id)
    ).group_by(Detection.source_type).all()

    # Average confidence
    avg_conf = db.session.query(func.avg(Detection.confidence)).scalar() or 0

    # Total with GPS
    geolocated = Detection.query.filter(Detection.latitude.isnot(None)).count()

    # Public reports
    pending_reports = PublicReport.query.filter_by(status='pending').count()
    total_reports = PublicReport.query.count()

    return jsonify({
        'total_detections': total,
        'by_damage_type': [{'type': t, 'label': l, 'count': c} for t, l, c in type_counts],
        'by_status': {s: c for s, c in status_counts if s},
        'by_source': {s: c for s, c in source_counts if s},
        'avg_confidence': round(float(avg_conf), 4),
        'total_geolocated': geolocated,
        'pending_reports': pending_reports,
        'total_reports': total_reports,
    }), 200
