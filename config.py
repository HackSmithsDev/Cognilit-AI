import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Config:
    """Base configuration settings for CogniLit AI."""
    # --- Core Flask & Security ---
    SECRET_KEY = os.getenv('SECRET_KEY', 'cognilit-dev-secret')
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # --- Database (PostgreSQL) ---
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Redis Cache ---
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # --- AI Services ---
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_MODEL = os.getenv('GROQ_MODEL')

    # --- File Upload Configuration ---
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    # --- Titan Mail (SMTP_SSL) Settings ---
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.titan.email')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_FROM = os.getenv('MAIL_FROM', os.getenv('MAIL_USERNAME'))
    MAIL_FROM_NAME = os.getenv('MAIL_FROM_NAME', 'CogniLit AI')
    MAIL_ADMIN_ADDRESS = os.getenv('MAIL_ADMIN_ADDRESS')

    # --- Flask-Executor (Background Tasks) ---
    EXECUTOR_TYPE = 'thread'
    EXECUTOR_MAX_WORKERS = 10
    EXECUTOR_PROPAGATE_EXCEPTIONS = True

    @staticmethod
    def init_app(app):
        """Handle setup tasks like directory creation for CogniLit."""
        subfolders = ['user_avatars', 'images', 'documents']
        for folder in subfolders:
            path = os.path.join(Config.UPLOAD_FOLDER, folder)
            os.makedirs(path, exist_ok=True)


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}