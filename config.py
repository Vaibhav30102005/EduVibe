import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # 🔐 Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'

    # 🛢️ Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📧 Mail Settings
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'your_email@gmail.com'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'your_email_password'
    MAIL_DEFAULT_SENDER = MAIL_USERNAME

    # 📁 File Uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size

    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    NOTES_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'notes')
    CERTIFICATE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'certificates')
    RESUME_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
    LEAVE_DOCS_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'leave_docs')

    # ✅ Allowed extensions
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
