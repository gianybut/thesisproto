"""Database models for the Road Damage Detection System."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

# The two system roles of the thesis (Chapter 3, Sec 3.5 and Fig. 3.5.1). A system
# administrator can do everything road maintenance personnel can, plus the admin-only tasks:
# manage accounts, manage (correct or delete) detections, see every survey, and read the
# activity log. Older databases used barangay/municipal/provincial/public/inspector;
# migrate.py maps all of those to 'personnel'.
ROLES = {
    'personnel': 'Road maintenance personnel',
    'admin': 'System administrator',
}
VALID_ROLES = list(ROLES)

# Account states. 'inactive' blocks sign-in and ends existing sign-ins on their next request
# (auth_tokens.verify_request). 'pending'/'rejected' were for the removed self-registration.
ACCOUNT_STATUSES = ['active', 'inactive']

# The four CRDDC 2022 evaluation classes, using RDD2022's own codes (Arya et al., 2022).
# Note: there is no D30 in RDD2022 — D00 is longitudinal, D10 transverse, D20 alligator.
DAMAGE_TYPES = {
    'D00': 'Longitudinal Crack',
    'D10': 'Transverse Crack',
    'D20': 'Alligator Crack',
    'D40': 'Pothole',
}

# Valid inspection/maintenance statuses
INSPECTION_STATUSES = [
    'pending_validation',
    'inspected',
    'scheduled',
    'ongoing_repair',
    'resolved',
]

# Where a detection's coordinates came from
POSITION_SOURCES = ['gps_file', 'georeferenced', 'none']


class User(db.Model):
    """User account: road maintenance personnel or system administrator (ROLES)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    lgu_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='personnel')  # one of ROLES
    agency = db.Column(db.String(200), nullable=True)
    sector_level = db.Column(db.String(50), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Account approval fields
    account_status = db.Column(db.String(20), default='active')  # active, pending, rejected
    id_photo = db.Column(db.String(300), nullable=True)  # filename of uploaded government ID
    rejection_reason = db.Column(db.String(500), nullable=True)

    videos = db.relationship('Video', backref='uploader', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        # pbkdf2 rather than werkzeug's scrypt default: macOS system Python is built
        # against LibreSSL, whose hashlib has no scrypt.
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'lgu_name': self.lgu_name,
            'role': self.role,
            'role_label': ROLES.get(self.role, ROLES['personnel']),
            'agency': self.agency,
            'sector_level': self.sector_level,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'account_status': self.account_status,
            'id_photo': self.id_photo,
            'rejection_reason': self.rejection_reason,
        }


class Video(db.Model):
    """Uploaded road survey video with optional GPS track."""
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
    display_name = db.Column(db.String(300), nullable=True)  # user-chosen label; falls back to original_filename
    file_size = db.Column(db.Integer)  # in bytes
    duration = db.Column(db.Float)  # in seconds
    fps = db.Column(db.Float)
    resolution = db.Column(db.String(20))  # e.g. "1920x1080"
    status = db.Column(db.String(30), default='uploaded')  # uploaded, processing, completed, failed
    processing_progress = db.Column(db.Float, default=0.0)  # 0-100
    upload_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    processed_date = db.Column(db.DateTime, nullable=True)
    processed_filename = db.Column(db.String(300), nullable=True)
    total_detections = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # GPS track file fields
    gps_filename = db.Column(db.String(300), nullable=True)
    gps_original_filename = db.Column(db.String(300), nullable=True)
    time_offset = db.Column(db.Float, default=0.0)  # seconds offset between video and GPS start
    road_name = db.Column(db.String(300), nullable=True)

    # How detections were positioned: gps_file (uploaded track), georeferenced (manual control points), none
    position_source = db.Column(db.String(20), default='none')

    # Why the analysis failed, in words a user can act on (set with status='failed').
    error_message = db.Column(db.String(500), nullable=True)

    detections = db.relationship('Detection', backref='video', lazy=True, cascade='all, delete-orphan')
    gps_track_points = db.relationship('GpsTrackPoint', backref='video', lazy=True, cascade='all, delete-orphan')
    control_points = db.relationship('RouteControlPoint', backref='video', lazy=True, cascade='all, delete-orphan',
                                     order_by='RouteControlPoint.video_time_s')

    @property
    def name(self):
        """What the user should see: their own label, or the uploaded filename."""
        return self.display_name or self.original_filename

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'display_name': self.display_name,
            'name': self.name,
            'file_size': self.file_size,
            'duration': self.duration,
            'fps': self.fps,
            'resolution': self.resolution,
            'status': self.status,
            'processing_progress': self.processing_progress,
            'error_message': self.error_message if self.status == 'failed' else None,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'total_detections': self.total_detections,
            'user_id': self.user_id,
            'uploaded_by': (self.uploader.full_name or self.uploader.username) if self.uploader else None,
            'gps_filename': self.gps_filename,
            'gps_original_filename': self.gps_original_filename,
            'time_offset': self.time_offset,
            'road_name': self.road_name,
            'has_gps': self.gps_filename is not None,
            'position_source': self.position_source or 'none',
            'control_point_count': len(self.control_points),
        }


class Detection(db.Model):
    """Individual road damage detection record with geo-location."""
    __tablename__ = 'detections'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    frame_number = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # seconds into the video
    confidence = db.Column(db.Float, nullable=False)
    bbox_x1 = db.Column(db.Float, nullable=False)
    bbox_y1 = db.Column(db.Float, nullable=False)
    bbox_x2 = db.Column(db.Float, nullable=False)
    bbox_y2 = db.Column(db.Float, nullable=False)
    frame_snapshot = db.Column(db.String(300), nullable=True)  # path to frame image
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Damage classification
    damage_type = db.Column(db.String(50), default='D40')  # D00, D10, D20, D40 (RDD2022 codes)
    damage_label = db.Column(db.String(100), default='Pothole')

    # GPS coordinates (populated when GPS track file is provided)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    position_source = db.Column(db.String(20), nullable=True)  # gps_file, georeferenced, none

    # Legacy columns from the dropped severity feature. Never written or read any more and not
    # exposed by to_dict(); kept only so existing databases need no destructive migration.
    severity = db.Column(db.String(20), nullable=True)
    severity_score = db.Column(db.Float, nullable=True)

    # Road and location info
    road_name = db.Column(db.String(300), nullable=True)

    # Maintenance workflow tracking
    inspection_status = db.Column(db.String(50), default='pending_validation')
    repair_status = db.Column(db.String(50), nullable=True)

    # Source tracking
    source_type = db.Column(db.String(30), default='ai_detection')  # ai_detection, public_report

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'frame_number': self.frame_number,
            'timestamp': self.timestamp,
            'timestamp_formatted': self._format_timestamp(),
            'confidence': round(self.confidence, 4),
            'bbox': {
                'x1': self.bbox_x1,
                'y1': self.bbox_y1,
                'x2': self.bbox_x2,
                'y2': self.bbox_y2
            },
            'frame_snapshot': self.frame_snapshot,
            'damage_type': self.damage_type,
            'damage_label': self.damage_label,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'position_source': self.position_source,
            'road_name': self.road_name,
            'inspection_status': self.inspection_status,
            'repair_status': self.repair_status,
            'source_type': self.source_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def _format_timestamp(self):
        """Convert seconds to MM:SS.ms format."""
        minutes = int(self.timestamp // 60)
        seconds = self.timestamp % 60
        return f"{minutes:02d}:{seconds:05.2f}"


class GpsTrackPoint(db.Model):
    """Individual GPS track point from an uploaded GPX/CSV file."""
    __tablename__ = 'gps_track_points'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    timestamp = db.Column(db.Float, nullable=False)  # seconds from track start
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    elevation = db.Column(db.Float, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'timestamp': self.timestamp,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'elevation': self.elevation,
        }


class RouteControlPoint(db.Model):
    """Manually placed (video time -> map coordinate) pair used to georeference a video with no GPS track."""
    __tablename__ = 'route_control_points'

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey('videos.id'), nullable=False)
    seq = db.Column(db.Integer, nullable=False)  # 0-based order by video_time_s
    video_time_s = db.Column(db.Float, nullable=False)  # seconds from video start
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'video_id': self.video_id,
            'seq': self.seq,
            'video_time_s': self.video_time_s,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class PublicReport(db.Model):
    """Citizen-submitted road damage report."""
    __tablename__ = 'public_reports'

    id = db.Column(db.Integer, primary_key=True)
    reporter_name = db.Column(db.String(150), nullable=True)
    reporter_contact = db.Column(db.String(200), nullable=True)
    image_filename = db.Column(db.String(300), nullable=True)
    description = db.Column(db.Text, nullable=True)

    # Location (GPS or manual)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    manual_location = db.Column(db.String(500), nullable=True)

    # Damage info
    damage_type = db.Column(db.String(50), default='D40')
    damage_label = db.Column(db.String(100), default='Pothole')

    # Status tracking
    status = db.Column(db.String(30), default='pending')  # pending, validated, rejected
    validated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationship to the user who submitted (if logged in)
    submitted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'reporter_name': self.reporter_name,
            'reporter_contact': self.reporter_contact,
            'image_filename': self.image_filename,
            'description': self.description,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'manual_location': self.manual_location,
            'damage_type': self.damage_type,
            'damage_label': self.damage_label,
            'status': self.status,
            'validated_by': self.validated_by,
            'rejection_reason': self.rejection_reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'submitted_by': self.submitted_by,
        }


class ActivityLog(db.Model):
    """Who did what, and when: the "View system logs" use case (thesis Fig. 3.5.1).

    Written by services/activity.py from the routes; read only by a system administrator
    (GET /api/activity). The username and summary are copied in at the time, so an entry
    still reads correctly after the account or the survey is renamed or removed.
    """
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # null: failed sign-in, system
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(40), nullable=False, index=True)  # see services/activity.py ACTIONS
    target_type = db.Column(db.String(30), nullable=True)  # survey, detection, account, report, export
    target_id = db.Column(db.Integer, nullable=True)
    summary = db.Column(db.String(500), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id,
            'username': self.username,
            'action': self.action,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'summary': self.summary,
        }
