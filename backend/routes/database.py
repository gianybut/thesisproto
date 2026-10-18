"""Centralized database routes — damage records management and export.

Both roles can read every record, change its inspection status and export the list.
Correcting a record (kind of damage, road name, repair note) and deleting one are the
"Manage detections" use case and are admin only (thesis Fig. 3.5.1).
"""

import csv
import io
import json
import os
from flask import Blueprint, request, jsonify, Response, current_app
from models import db, Video, Detection, PublicReport, DAMAGE_TYPES, INSPECTION_STATUSES
from auth_tokens import admin_required, can_open_video, current_user_id as get_user_id, is_admin
from services.activity import record
from sqlalchemy import func

STATUS_NAMES = {
    'pending_validation': 'Not yet checked',
    'inspected': 'Checked on site',
    'scheduled': 'Repair scheduled',
    'ongoing_repair': 'Repair under way',
    'resolved': 'Repaired',
}


def _record_dict(d):
    """A detection as the records page needs it: plus whether the caller may open its survey."""
    row = d.to_dict()
    row['can_open_video'] = bool(d.video and d.source_type != 'public_report' and can_open_video(d.video.user_id))
    return row


def _describe(d):
    return f'record #{d.id} ({DAMAGE_TYPES.get(d.damage_type, d.damage_label or "damage").lower()}' + \
        (f', {d.road_name})' if d.road_name else ')')

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
        'detections': [_record_dict(d) for d in detections]
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

    # Road name and repair note are corrections, which only an administrator makes.
    if ('road_name' in data or 'repair_status' in data) and not is_admin():
        return jsonify({'error': 'Only a system administrator can correct a damage record.', 'code': 'admin_only'}), 403

    old_status = detection.inspection_status
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
    if new_status and new_status != old_status:
        record('status_changed', f'Marked {_describe(detection)} "{STATUS_NAMES.get(new_status, new_status)}" '
               f'(was "{STATUS_NAMES.get(old_status, old_status)}")', target_type='detection', target_id=detection.id)

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
    record('data_exported', f'Downloaded {len(data)} damage records as {"JSON" if format_type == "json" else "CSV"}',
           target_type='export')

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


@database_bp.route('/detections/<int:detection_id>', methods=['PATCH'])
@admin_required
def correct_detection(detection_id):
    """Admin: correct a record. Body: any of {damage_type, road_name}."""
    detection = Detection.query.get(detection_id)
    if not detection:
        return jsonify({'error': 'That damage record no longer exists.'}), 404

    data = request.get_json(silent=True) or {}
    before = _describe(detection)
    changes = []

    if 'damage_type' in data and data['damage_type'] != detection.damage_type:
        code = data['damage_type']
        if code not in DAMAGE_TYPES:
            return jsonify({'error': 'Choose one of the four kinds of damage.'}), 400
        changes.append(f'kind of damage to {DAMAGE_TYPES[code].lower()}')
        detection.damage_type = code
        detection.damage_label = DAMAGE_TYPES[code]

    if 'road_name' in data:
        road = (data.get('road_name') or '').strip() or None
        if road != detection.road_name:
            changes.append(f'road name to "{road}"' if road else 'removed the road name')
            detection.road_name = road

    if changes:
        db.session.commit()
        record('detection_corrected', f'Corrected {before}: {", ".join(changes)}',
               target_type='detection', target_id=detection.id)
    return jsonify({'message': 'Saved.' if changes else 'Nothing changed.', 'detection': _record_dict(detection)}), 200


@database_bp.route('/detections/<int:detection_id>', methods=['DELETE'])
@admin_required
def delete_detection(detection_id):
    """Admin: delete a record (a false detection), with its snapshot."""
    detection = Detection.query.get(detection_id)
    if not detection:
        return jsonify({'error': 'That damage record no longer exists.'}), 404

    summary = f'Deleted {_describe(detection)}'
    if detection.frame_snapshot:
        snap = os.path.join(current_app.config['SNAPSHOTS_FOLDER'], detection.frame_snapshot)
        if os.path.exists(snap):
            os.remove(snap)
    video = detection.video
    if video and video.total_detections:
        video.total_detections -= 1
        summary += f' from "{video.name}"'
    db.session.delete(detection)
    db.session.commit()
    record('detection_deleted', summary, target_type='detection', target_id=detection_id)
    return jsonify({'message': 'Record deleted.'}), 200


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
