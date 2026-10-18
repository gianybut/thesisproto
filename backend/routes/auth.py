"""Authentication routes: sign in, who am I, sign out.

There is no self-registration: a system administrator creates accounts (routes/accounts.py,
thesis Fig. 3.5.1 "Manage user accounts").
"""

from flask import Blueprint, request, jsonify, current_app
from models import User
from auth_tokens import current_user, issue_token
from services.activity import record

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate a user."""
    data = request.get_json(silent=True)

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if user is None or not user.check_password(data['password']):
        record('sign_in_failed', f"Wrong username or password for \"{data['username'][:80]}\"",
               target_type='account', target_id=user.id if user else None, username=data['username'][:80])
        return jsonify({'error': 'Invalid username or password'}), 401

    if user.account_status != 'active':
        record('sign_in_failed', f'{user.username} tried to sign in to an inactive account',
               target_type='account', target_id=user.id, user=user)
        return jsonify({
            'error': 'This account has been turned off. Ask your system administrator to turn it back on.',
            'account_status': user.account_status,
        }), 403

    token, expires_at = issue_token(user, current_app.config)
    client = 'phone app' if request.headers.get('X-Client') == 'mobile' else 'web app'
    record('sign_in', f'{user.username} signed in on the {client}', target_type='account', target_id=user.id, user=user)
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'expires_at': expires_at,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get the user the bearer token belongs to (verified in auth_tokens.verify_request)."""
    return jsonify({'user': current_user().to_dict()}), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Tokens are stateless: logging out is the client discarding its token.
    They stay valid until they expire (JWT_EXPIRY_HOURS)."""
    return jsonify({'message': 'Logged out successfully'}), 200
