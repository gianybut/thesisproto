"""Account management: the "Manage user accounts" use case (thesis Fig. 3.5.1). Admin only.

A system administrator creates accounts, changes their name or role, turns them off and on,
and resets passwords. Accounts are never deleted: turning one off keeps its surveys and its
history in the activity log, and stops it signing in (auth_tokens.verify_request rejects an
inactive account on its very next request).
"""

from flask import Blueprint, request, jsonify
from sqlalchemy import func
from models import db, User, Video, ROLES, ACCOUNT_STATUSES
from auth_tokens import admin_required, current_user
from services.activity import record

accounts_bp = Blueprint('accounts', __name__)

MIN_PASSWORD = 8


def _account_dict(user, survey_counts):
    d = user.to_dict()
    d['survey_count'] = survey_counts.get(user.id, 0)
    d.pop('id_photo', None)
    d.pop('rejection_reason', None)
    return d


def _survey_counts():
    return dict(db.session.query(Video.user_id, func.count(Video.id)).group_by(Video.user_id).all())


def _active_admins_other_than(user_id):
    return User.query.filter(User.role == 'admin', User.account_status == 'active', User.id != user_id).count()


@accounts_bp.route('', methods=['GET'])
@admin_required
def list_accounts():
    users = User.query.order_by(User.full_name).all()
    counts = _survey_counts()
    return jsonify({
        'accounts': [_account_dict(u, counts) for u in users],
        'roles': [{'value': k, 'label': v} for k, v in ROLES.items()],
    }), 200


@accounts_bp.route('', methods=['POST'])
@admin_required
def create_account():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    full_name = (data.get('full_name') or '').strip()
    password = data.get('password') or ''
    role = data.get('role') or 'personnel'

    errors = {}
    if not username:
        errors['username'] = 'Enter a username'
    elif len(username) > 80 or not username.replace('.', '').replace('_', '').replace('-', '').isalnum():
        errors['username'] = 'Use up to 80 letters, numbers, dots, dashes or underscores, with no spaces'
    elif User.query.filter(func.lower(User.username) == username.lower()).first():
        errors['username'] = f'The username "{username}" is already taken. Choose another.'
    if not full_name:
        errors['full_name'] = 'Enter the person\'s full name'
    if len(password) < MIN_PASSWORD:
        errors['password'] = f'The password must be at least {MIN_PASSWORD} characters'
    if role not in ROLES:
        errors['role'] = 'Choose a role'
    if errors:
        return jsonify({'error': 'Check the highlighted fields.', 'fields': errors}), 400

    admin = current_user()
    user = User(
        username=username,
        full_name=full_name,
        email=(data.get('email') or '').strip() or None,
        role=role,
        # The office comes from the administrator creating the account; the UI never shows it.
        lgu_name=admin.lgu_name,
        agency=admin.agency,
        sector_level=admin.sector_level,
        account_status='active',
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    record('account_created', f'Created {ROLES[role].lower()} account "{username}" ({full_name})',
           target_type='account', target_id=user.id)
    return jsonify({'message': f'Created the account for {full_name}.', 'account': _account_dict(user, {})}), 201


@accounts_bp.route('/<int:user_id>', methods=['PATCH'])
@admin_required
def update_account(user_id):
    """Body: any of {full_name, email, role, account_status}."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'That account no longer exists.'}), 404

    data = request.get_json(silent=True) or {}
    me = current_user()
    changes = []

    if 'full_name' in data:
        name = (data.get('full_name') or '').strip()
        if not name:
            return jsonify({'error': 'Enter the person\'s full name', 'fields': {'full_name': 'Enter the person\'s full name'}}), 400
        if name != user.full_name:
            changes.append(f'name to "{name}"')
            user.full_name = name

    if 'email' in data:
        email = (data.get('email') or '').strip() or None
        if email != user.email:
            changes.append('email')
            user.email = email

    if 'role' in data and data['role'] != user.role:
        role = data['role']
        if role not in ROLES:
            return jsonify({'error': 'Choose a role', 'fields': {'role': 'Choose a role'}}), 400
        if user.id == me.id:
            return jsonify({'error': 'You cannot change your own role. Ask another system administrator.'}), 400
        if user.role == 'admin' and not _active_admins_other_than(user.id):
            return jsonify({'error': 'This is the only active system administrator. Make another account an administrator first.'}), 400
        changes.append(f'role to {ROLES[role].lower()}')
        user.role = role

    if 'account_status' in data and data['account_status'] != user.account_status:
        status = data['account_status']
        if status not in ACCOUNT_STATUSES:
            return jsonify({'error': 'Account status must be active or inactive'}), 400
        if status == 'inactive':
            if user.id == me.id:
                return jsonify({'error': 'You cannot turn off your own account.'}), 400
            if user.role == 'admin' and not _active_admins_other_than(user.id):
                return jsonify({'error': 'This is the only active system administrator, so it cannot be turned off.'}), 400
        changes.append('turned off' if status == 'inactive' else 'turned back on')
        user.account_status = status

    if not changes:
        return jsonify({'message': 'Nothing changed.', 'account': _account_dict(user, _survey_counts())}), 200

    db.session.commit()
    record('account_updated', f'Changed account "{user.username}": {", ".join(changes)}',
           target_type='account', target_id=user.id)
    return jsonify({'message': f'Saved the changes to {user.full_name}.', 'account': _account_dict(user, _survey_counts())}), 200


@accounts_bp.route('/<int:user_id>/password', methods=['PUT'])
@admin_required
def reset_password(user_id):
    """Body: {password}. Existing sign-ins on that account stay valid until they expire."""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'That account no longer exists.'}), 404
    password = (request.get_json(silent=True) or {}).get('password') or ''
    if len(password) < MIN_PASSWORD:
        msg = f'The password must be at least {MIN_PASSWORD} characters'
        return jsonify({'error': msg, 'fields': {'password': msg}}), 400
    user.set_password(password)
    db.session.commit()
    record('password_reset', f'Reset the password of "{user.username}"', target_type='account', target_id=user.id)
    return jsonify({'message': f'Set a new password for {user.full_name}. Give it to them in person.'}), 200
