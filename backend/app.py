"""Flask application factory for the Pothole Detection System."""

import os
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
    app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
    app.config['MODEL_PATH'] = os.path.join(base_dir, '..', 'ml', 'models', 'best.pt')

    # Ensure directories exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], app.config['SNAPSHOTS_FOLDER']]:
        os.makedirs(folder, exist_ok=True)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Register blueprints
    from routes.auth import auth_bp
    from routes.videos import videos_bp
    from routes.detections import detections_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(videos_bp, url_prefix='/api/videos')
    app.register_blueprint(detections_bp, url_prefix='/api')

    # Create database tables
    with app.app_context():
        db.create_all()

        # Create default admin user if none exists
        from models import User
        if not User.query.first():
            admin = User(
                username='admin',
                full_name='System Administrator',
                lgu_name='Default LGU',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default admin user created (username: admin, password: admin123)")

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
