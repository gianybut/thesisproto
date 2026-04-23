"""Database models for the Pothole Detection System."""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(db.Model):
    """LGU personnel user account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    lgu_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='inspector')  # inspector, admin
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    videos = db.relationship('Video', backref='uploader', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'lgu_name': self.lgu_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Video(db.Model):
    """Uploaded road survey video."""
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300), nullable=False)
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

    detections = db.relationship('Detection', backref='video', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'duration': self.duration,
            'fps': self.fps,
            'resolution': self.resolution,
            'status': self.status,
            'processing_progress': self.processing_progress,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'total_detections': self.total_detections,
            'user_id': self.user_id
        }


class Detection(db.Model):
    """Individual pothole detection record."""
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
            'frame_snapshot': self.frame_snapshot
        }

    def _format_timestamp(self):
        """Convert seconds to MM:SS.ms format."""
        minutes = int(self.timestamp // 60)
        seconds = self.timestamp % 60
        return f"{minutes:02d}:{seconds:05.2f}"
