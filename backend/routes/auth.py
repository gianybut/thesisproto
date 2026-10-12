"""Authentication routes — supports role-based access hierarchy."""

from flask import Blueprint, request, jsonify, current_app
from models import db, User, VALID_ROLES
from auth_tokens import current_user, issue_token
from werkzeug.utils import secure_filename
import os
import uuid

auth_bp = Blueprint('auth', __name__)

# Roles that require ID verification and admin approval
APPROVAL_REQUIRED_ROLES = ['barangay', 'municipal', 'inspector']

# Roles available for self-registration (admin/provincial assigned by admin only)
SELF_REGISTER_ROLES = ['public', 'barangay', 'municipal', 'inspector']

ALLOWED_ID_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}


def _allowed_id_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_ID_EXTENSIONS


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user is None or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Block login for non-active accounts
    if user.account_status == 'pending':
        return jsonify({
            'error': 'Your account is pending verification by a system administrator. '
                     'Please wait for approval before logging in.',
            'account_status': 'pending'
        }), 403

    if user.account_status == 'rejected':
        reason = user.rejection_reason or 'No reason provided'
        return jsonify({
            'error': f'Your account registration was rejected. Reason: {reason}',
            'account_status': 'rejected'
        }), 403

    token, expires_at = issue_token(user, current_app.config)
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'expires_at': expires_at,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account with role assignment.
    
    For government roles (barangay, municipal, inspector), requires an ID photo
    upload and sets account_status to 'pending' for admin approval.
    Public users get instant access.
    """
    # Handle both JSON and multipart form data (needed for file uploads)
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form.to_dict()
        id_file = request.files.get('id_photo')
    else:
        data = request.get_json() or {}
        id_file = None

    required_fields = ['username', 'password', 'full_name', 'lgu_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    # Validate role — only allow self-registration for non-privileged roles.
    role = data.get('role', 'public')
    if role not in SELF_REGISTER_ROLES:
        return jsonify({
            'error': f'Cannot self-register as "{role}". '
                     f'Admin and Provincial accounts must be assigned by a system administrator.'
        }), 403

    # Determine account status based on role
    if role in APPROVAL_REQUIRED_ROLES:
        account_status = 'pending'

        # Require ID photo for government roles
        if not id_file:
            return jsonify({
                'error': 'A government ID photo is required for this role. '
                         'Please upload a valid ID to verify your identity.'
            }), 400

        if not _allowed_id_file(id_file.filename):
            return jsonify({
                'error': 'Invalid file type. Please upload a JPG, PNG, or PDF file.'
            }), 400

        # Save the ID photo
        ext = id_file.filename.rsplit('.', 1)[1].lower()
        id_filename = f"id_{uuid.uuid4().hex[:12]}.{ext}"
        id_photos_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'uploads'), 'id_photos')
        os.makedirs(id_photos_dir, exist_ok=True)
        id_file.save(os.path.join(id_photos_dir, id_filename))
    else:
        account_status = 'active'
        id_filename = None

    user = User(
        username=data['username'],
        full_name=data['full_name'],
        lgu_name=data['lgu_name'],
        role=role,
        agency=data.get('agency', ''),
        sector_level=data.get('sector_level', ''),
        email=data.get('email', ''),
        account_status=account_status,
        id_photo=id_filename,
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    if account_status == 'pending':
        return jsonify({
            'message': 'Registration submitted! Your account is pending verification by a system administrator. '
                       'You will be able to log in once your identity has been verified.',
            'account_status': 'pending',
        }), 201
    else:
        # Public users get instant access
        token, expires_at = issue_token(user, current_app.config)
        return jsonify({
            'message': 'Registration successful',
            'token': token,
            'expires_at': expires_at,
            'user': user.to_dict()
        }), 201


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get the user the bearer token belongs to (verified in auth_tokens.verify_request)."""
    return jsonify({'user': current_user().to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Tokens are stateless: logging out is the client discarding its token.
    They stay valid until they expire (JWT_EXPIRY_HOURS)."""
    return jsonify({'message': 'Logged out successfully'}), 200
