"""Activity log: the "View system logs" use case (thesis Fig. 3.5.1). Admin only."""

from flask import Blueprint, request, jsonify
from models import ActivityLog, User
from auth_tokens import admin_required
from services.activity import ACTIONS

activity_bp = Blueprint('activity', __name__)


@activity_bp.route('', methods=['GET'])
@admin_required
def list_activity():
    """Newest first. Query: action, user_id, page, per_page (max 100)."""
    query = ActivityLog.query

    action = request.args.get('action')
    if action:
        query = query.filter(ActivityLog.action == action)
    user_id = request.args.get('user_id', type=int)
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)

    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(max(1, request.args.get('per_page', 50, type=int)), 100)
    total = query.count()
    rows = query.order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc()) \
        .offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        'entries': [r.to_dict() for r in rows],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': max(1, (total + per_page - 1) // per_page),
        'actions': [{'value': k, 'label': v} for k, v in ACTIONS.items()],
        'users': [{'id': u.id, 'name': u.full_name or u.username} for u in User.query.order_by(User.full_name).all()],
    }), 200
