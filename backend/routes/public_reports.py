"""Public reporting routes — citizen-submitted road damage reports."""

import os
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db, PublicReport, Detection, DAMAGE_TYPES
from auth_tokens import admin_required, current_user_id as get_user_id
from services.activity import record

public_reports_bp = Blueprint('public_reports', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp', 'heic'}


def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


@public_reports_bp.route('', methods=['POST'])
def submit_report():
    """Submit a new public road damage report."""
    user_id = get_user_id()  # Optional — public users may not be logged in

    # Parse form data
    reporter_name = request.form.get('reporter_name', '')
    reporter_contact = request.form.get('reporter_contact', '')
    description = request.form.get('description', '')
    latitude = request.form.get('latitude', type=float)
    longitude = request.form.get('longitude', type=float)
    manual_location = request.form.get('manual_location', '')
    damage_type = request.form.get('damage_type', 'D40')
    damage_label = DAMAGE_TYPES.get(damage_type, 'Pothole')

    # Validate location — must have either GPS or manual
    if not latitude and not longitude and not manual_location:
        return jsonify({'error': 'Location is required. Provide GPS coordinates or a manual location description.'}), 400

    # Handle image upload
    image_filename = None
    if 'image' in request.files:
        image = request.files['image']
        if image.filename and image.filename != '':
            if not allowed_image(image.filename):
                return jsonify({
                    'error': f'Image type not allowed. Supported: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
                }), 400

            original_name = secure_filename(image.filename)
            ext = original_name.rsplit('.', 1)[1].lower()
            image_filename = f"report_{uuid.uuid4().hex}.{ext}"
            image_path = os.path.join(current_app.config['REPORTS_FOLDER'], image_filename)
            image.save(image_path)

    report = PublicReport(
        reporter_name=reporter_name,
        reporter_contact=reporter_contact,
        image_filename=image_filename,
        description=description,
        latitude=latitude,
        longitude=longitude,
        manual_location=manual_location,
        damage_type=damage_type,
        damage_label=damage_label,
        status='pending',
        submitted_by=user_id,
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({
        'message': 'Report submitted successfully. It will be reviewed by local authorities.',
        'report': report.to_dict()
    }), 201


@public_reports_bp.route('', methods=['GET'])
def list_reports():
    """List all public reports with optional status filter."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    query = PublicReport.query

    status = request.args.get('status')
    if status:
        query = query.filter(PublicReport.status == status)

    reports = query.order_by(PublicReport.created_at.desc()).all()

    return jsonify({
        'total': len(reports),
        'reports': [r.to_dict() for r in reports]
    }), 200


@public_reports_bp.route('/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """Get a single report by ID."""
    report = PublicReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    return jsonify({'report': report.to_dict()}), 200


@public_reports_bp.route('/<int:report_id>/validate', methods=['PUT'])
@admin_required
def validate_report(report_id):
    """Validate a public report — converts to official detection record. Admin only
    ("Manage detections"), because it adds a record every role then sees."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    report = PublicReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    if report.status == 'validated':
        return jsonify({'error': 'Report already validated'}), 400

    report.status = 'validated'
    report.validated_by = user_id

    # Create a detection record from the public report
    if report.latitude and report.longitude:
        detection = Detection(
            video_id=0,  # No video for public reports
            frame_number=0,
            timestamp=0,
            confidence=0.5,  # Default confidence for public reports
            bbox_x1=0, bbox_y1=0, bbox_x2=0, bbox_y2=0,
            damage_type=report.damage_type,
            damage_label=report.damage_label,
            latitude=report.latitude,
            longitude=report.longitude,
            road_name=report.manual_location,
            inspection_status='pending_validation',
            source_type='public_report',
            frame_snapshot=report.image_filename,
        )
        db.session.add(detection)

    db.session.commit()
    record('report_validated', f'Accepted resident report #{report.id} ({report.damage_label or "damage"})',
           target_type='report', target_id=report.id)

    return jsonify({
        'message': 'Report validated and added to damage database.',
        'report': report.to_dict()
    }), 200


@public_reports_bp.route('/<int:report_id>/reject', methods=['PUT'])
@admin_required
def reject_report(report_id):
    """Reject a public report."""
    user_id = get_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401

    data = request.get_json() or {}

    report = PublicReport.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404

    report.status = 'rejected'
    report.validated_by = user_id
    report.rejection_reason = data.get('reason', '')
    db.session.commit()
    record('report_rejected', f'Rejected resident report #{report.id}', target_type='report', target_id=report.id)

    return jsonify({
        'message': 'Report rejected.',
        'report': report.to_dict()
    }), 200


@public_reports_bp.route('/image/<path:filename>', methods=['GET'])
def get_report_image(filename):
    """Serve a report image."""
    from flask import send_file
    file_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'Image not found'}), 404
    return send_file(file_path)
