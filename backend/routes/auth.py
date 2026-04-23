"""Authentication routes for LGU personnel."""

from flask import Blueprint, request, jsonify, session
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user."""
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user is None or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401

    session['user_id'] = user.id
    return jsonify({
        'message': 'Login successful',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new LGU user account."""
    data = request.get_json()

    required_fields = ['username', 'password', 'full_name', 'lgu_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409

    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400

    user = User(
        username=data['username'],
        full_name=data['full_name'],
        lgu_name=data['lgu_name'],
        role=data.get('role', 'inspector')
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    return jsonify({
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get the currently authenticated user."""
    user_id = session.get('user_id')

    # Also check Authorization header for token-based auth
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            user_id = int(auth_header.split(' ')[1])
        except (ValueError, IndexError):
            pass

    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Log out the current user."""
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out successfully'}), 200
