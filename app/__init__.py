# app/__init__.py

from flask import Flask, request, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sendgrid import SendGridAPIClient
from dotenv import load_dotenv
import os

# ─────────────────────────────
# 🔹 Paths and Config
# ─────────────────────────────
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads/portfolio')

# ─────────────────────────────
# 🔹 Initialize Extensions
# ─────────────────────────────
db = SQLAlchemy()
login_manager = LoginManager()


# ─────────────────────────────
# 🔹 App Factory Function
# ─────────────────────────────
def create_app():
    # ✅ Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # ✅ Core Configuration
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL", "sqlite:///eduvibe.db")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # ✅ Mail Configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")

    # ✅ File Upload Configuration
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
    app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'png', 'jpg', 'jpeg', 'docx'}

    # ✅ Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    

    # ✅ Login Configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # ✅ Register Blueprints
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.notes import notes_bp
    from .routes.planner import planner_bp
    from .routes.admin import bp as admin_bp
    from .routes.group_study import group_bp
    from .routes.attendance_routes import attendance_bp
    from .routes.feedback_routes import feedback_bp
    from .routes.doubt_routes import doubt_bp
    from .routes.complaint_routes import complaint_bp
    from .routes.routine_routes import routine_bp
    from .routes.cr_voting import cr_bp
    from .routes.portfolio_routes import portfolio_bp
    from .routes.leave import leave_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(doubt_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(routine_bp, url_prefix='/routine')
    app.register_blueprint(cr_bp, url_prefix='/cr')
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(leave_bp, url_prefix='/leave')

    # ✅ User Loader
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ✅ Handle Large File Uploads Gracefully
    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash("File is too large. Maximum allowed size is 10 MB.", "danger")
        return redirect(request.referrer or url_for('dashboard.index'))

    return app
