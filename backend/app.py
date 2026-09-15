"""Flask application factory for the Road Damage Detection System."""

import os
import shutil
from flask import Flask
from flask_cors import CORS
from models import db


def create_app():
    app = Flask(__name__)

    # Configuration
    base_dir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pothole-detection-secret-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'pothole_detection.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
    app.config['PROCESSED_FOLDER'] = os.path.join(base_dir, 'processed')
    app.config['SNAPSHOTS_FOLDER'] = os.path.join(base_dir, 'snapshots')
    app.config['REPORTS_FOLDER'] = os.path.join(base_dir, 'reports')
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
    app.config['MAX_VIDEO_DURATION_S'] = 10 * 60          # 10-minute cap (thesis Sec 1.7 / 3.4)
    app.config['MODEL_PATH'] = os.path.join(base_dir, '..', 'ml', 'models', 'best.pt')

    # Ensure directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'],
                   app.config['SNAPSHOTS_FOLDER'], app.config['REPORTS_FOLDER'],
                   os.path.join(app.config['UPLOAD_FOLDER'], 'id_photos')]:
        os.makedirs(folder, exist_ok=True)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.videos import videos_bp
    from routes.detections import detections_bp
    from routes.damage_map import damage_map_bp
    from routes.public_reports import public_reports_bp
    from routes.database import database_bp
    from routes.accounts import accounts_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(detections_bp, url_prefix='/api')
    app.register_blueprint(damage_map_bp, url_prefix='/api/map')
    app.register_blueprint(public_reports_bp, url_prefix='/api/reports')
    app.register_blueprint(database_bp, url_prefix='/api/database')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')

    # Processing runs in a plain thread that dies with the server. Anything still marked
    # 'uploaded' or 'processing' at boot was interrupted and will never finish — say so
    # instead of leaving it spinning forever in the UI.
    if shutil.which('ffmpeg') is None:
        print("⚠️  ffmpeg is not on PATH — annotated videos will be saved as AVI, which most "
              "browsers cannot play. Install it: winget install Gyan.FFmpeg")

    # Create database tables
    with app.app_context():
        db.create_all()

        from models import Video
        stale = Video.query.filter(Video.status.in_(['uploaded', 'processing'])).all()
        if stale:
            for v in stale:
                v.status = 'failed'
                v.processing_progress = 0
            db.session.commit()
            print(f"⚠️  Marked {len(stale)} interrupted upload(s) as failed (server restarted mid-processing)")

        # Create default admin user if none exists
        from models import User
        if not User.query.first():
            admin = User(
                username='admin',
                full_name='System Administrator',
                lgu_name='Local Government Unit of Mendez-Nuñez',
                role='admin',
                agency='Local Government Unit of Mendez-Nuñez',
                sector_level='municipal',
                account_status='active',
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
