"""Account management routes — admin-only approval workflow for government role registrations."""

from flask import Blueprint, request, jsonify, send_from_directory, current_app
from models import db, User
from auth_tokens import current_user
import os

accounts_bp = Blueprint('accounts', __name__)


def _require_admin():
    """Check that the current user is an admin. Returns (user, error_response)."""
    user = current_user()
    if not user:
        return None, (jsonify({'error': 'Not authenticated'}), 401)
    if user.role != 'admin':
        return None, (jsonify({'error': 'Admin access required'}), 403)
    return user, None


@accounts_bp.route('/pending', methods=['GET'])
def get_pending_accounts():
    """List all pending account registrations (admin only)."""
    admin, error = _require_admin()
    if error:
        return error

    pending = User.query.filter_by(account_status='pending').order_by(User.created_at.desc()).all()
    return jsonify({
        'accounts': [u.to_dict() for u in pending],
        'count': len(pending),
    }), 200


@accounts_bp.route('/all', methods=['GET'])
def get_all_accounts():
    """List all accounts with optional status filter (admin only)."""
    admin, error = _require_admin()
    if error:
        return error

    status = request.args.get('status')
    query = User.query

    if status:
        query = query.filter_by(account_status=status)

    accounts = query.order_by(User.created_at.desc()).all()
    return jsonify({
        'accounts': [u.to_dict() for u in accounts],
        'count': len(accounts),
    }), 200


@accounts_bp.route('/<int:user_id>/approve', methods=['PUT'])
def approve_account(user_id):
    """Approve a pending account registration (admin only)."""
    admin, error = _require_admin()
    if error:
        return error

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.account_status != 'pending':
        return jsonify({'error': f'Account is already {user.account_status}'}), 400

    user.account_status = 'active'
    user.rejection_reason = None
    db.session.commit()

    return jsonify({
        'message': f'Account for {user.full_name} has been approved.',
        'user': user.to_dict()
    }), 200


@accounts_bp.route('/<int:user_id>/reject', methods=['PUT'])
def reject_account(user_id):
    """Reject a pending account registration (admin only)."""
    admin, error = _require_admin()
    if error:
        return error

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if user.account_status != 'pending':
        return jsonify({'error': f'Account is already {user.account_status}'}), 400

    data = request.get_json() or {}
    reason = data.get('reason', 'Registration rejected by administrator')

    user.account_status = 'rejected'
    user.rejection_reason = reason
    db.session.commit()

    return jsonify({
        'message': f'Account for {user.full_name} has been rejected.',
        'user': user.to_dict()
    }), 200


@accounts_bp.route('/id-photo/<filename>', methods=['GET'])
def serve_id_photo(filename):
    """Serve an uploaded ID photo for admin review."""
    admin, error = _require_admin()
    if error:
        return error

    id_photos_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'id_photos')
    file_path = os.path.join(id_photos_dir, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'ID photo not found'}), 404

    return send_from_directory(id_photos_dir, filename)


@accounts_bp.route('/stats', methods=['GET'])
def get_account_stats():
    """Get account statistics (admin only)."""
    admin, error = _require_admin()
    if error:
        return error

    total = User.query.count()
    pending = User.query.filter_by(account_status='pending').count()
    active = User.query.filter_by(account_status='active').count()
    rejected = User.query.filter_by(account_status='rejected').count()

    return jsonify({
        'total': total,
        'pending': pending,
        'active': active,
        'rejected': rejected,
    }), 200
