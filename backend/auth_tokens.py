"""Signed bearer tokens (HS256 JWT) and the request hook that verifies them.

Every /api/* request passes through `verify_request`. Unless the endpoint is
listed in PUBLIC_ENDPOINTS, it must carry `Authorization: Bearer <jwt>` for an
existing, active user, or it gets a 401 before the route runs. Routes read the
caller with `current_user_id()` / `current_user()` instead of parsing headers.

Media endpoints (QUERY_TOKEN_ENDPOINTS) also accept `?token=<jwt>`, because a
browser <video>/<img> src cannot send an Authorization header.

Roles (models.ROLES) are enforced here on the server, not only by hiding pages:
`admin_required` guards the admin-only routes, and `visible_videos()` is the one place
that decides whose surveys a caller may see (an administrator sees every survey; road
maintenance personnel see their own).
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request
from sqlalchemy import true

from models import User, Video

ALGORITHM = 'HS256'
DEFAULT_EXPIRY_HOURS = 12

# No token needed. Anything not listed here requires one.
PUBLIC_ENDPOINTS = {
    'auth.login',
    'auth.logout',
    'public_reports.submit_report',  # anonymous citizen reports; a valid token is used if sent
}

QUERY_TOKEN_ENDPOINTS = {
    'videos.stream_original_video',
    'videos.stream_processed_video',
    'videos.get_snapshot',
    'public_reports.get_report_image',
}


def load_secret_key(base_dir):
    """SECRET_KEY from the environment, else a random key kept in backend/.secret_key.

    Never a hard-coded default: anyone with the repo could sign tokens with it.
    """
    env = os.environ.get('SECRET_KEY')
    if env:
        return env
    path = os.path.join(base_dir, '.secret_key')
    if os.path.exists(path):
        with open(path) as f:
            key = f.read().strip()
        if key:
            return key
    key = secrets.token_hex(32)
    with open(path, 'w') as f:
        f.write(key)
    return key


def issue_token(user, config):
    """Create a signed token for `user`. Returns (token, expires_at_iso)."""
    hours = float(config.get('JWT_EXPIRY_HOURS', DEFAULT_EXPIRY_HOURS))
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=hours)
    payload = {'sub': str(user.id), 'iat': now, 'exp': exp}
    token = jwt.encode(payload, config['SECRET_KEY'], algorithm=ALGORITHM)
    return token, exp.isoformat()


def _unauthorized(message, code):
    return jsonify({'error': message, 'code': code}), 401


def _read_token():
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:].strip()
    if request.endpoint in QUERY_TOKEN_ENDPOINTS:
        return request.args.get('token')
    return None


def verify_request(config):
    """before_request hook. Sets g.user (or None) and rejects unauthenticated calls."""
    g.user = None
    if request.method == 'OPTIONS' or not request.path.startswith('/api/'):
        return None

    public = request.endpoint in PUBLIC_ENDPOINTS
    token = _read_token()
    if not token:
        return None if public else _unauthorized('Authentication required.', 'token_missing')

    try:
        payload = jwt.decode(token, config['SECRET_KEY'], algorithms=[ALGORITHM],
                             options={'require': ['sub', 'exp', 'iat']})
        user_id = int(payload['sub'])
    except jwt.ExpiredSignatureError:
        return None if public else _unauthorized('Your session has expired. Log in again.', 'token_expired')
    except (jwt.InvalidTokenError, ValueError):
        return None if public else _unauthorized('Invalid session. Log in again.', 'token_invalid')

    user = User.query.get(user_id)
    if user is None or user.account_status != 'active':
        return None if public else _unauthorized('This account is no longer active.', 'user_inactive')

    g.user = user
    return None


def current_user():
    return g.get('user')


def current_user_id():
    user = g.get('user')
    return user.id if user else None


def is_admin():
    user = g.get('user')
    return bool(user and user.is_admin)


def admin_required(view):
    """Route decorator: 403 unless the caller is a system administrator."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_admin():
            return jsonify({'error': 'Only a system administrator can do this.', 'code': 'admin_only'}), 403
        return view(*args, **kwargs)
    return wrapper


def video_scope():
    """Filter clause for the surveys the caller may see: every survey for an admin, else their own.
    Use it in joins and aggregates; visible_videos() is the same as a ready query."""
    return true() if is_admin() else (Video.user_id == current_user_id())


def visible_videos():
    return Video.query.filter(video_scope())


def can_open_video(video_user_id):
    """Whether the caller may open a survey owned by `video_user_id` (see visible_videos)."""
    return is_admin() or video_user_id == current_user_id()
