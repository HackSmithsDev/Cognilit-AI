from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from .utils import generate_secret_id


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.String(20), primary_key=True, default=generate_secret_id)
    
    # Auth Fields
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False) # Changed to nullable=False for security
    
    # Profile Details
    profile_pic = db.Column(db.String(255), default='static/assets/avatars/default_profile_pic.png')
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    profession = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    reviews = db.relationship('Reviews', backref='user', lazy=True)

    projects = db.relationship('Project', backref='owner', lazy=True, cascade="all, delete-orphan")
    settings_data = db.relationship('SettingsData', backref='user', uselist=False, cascade="all, delete-orphan")
    saved_documents = db.relationship('SavedDocument', backref='user', lazy=True, cascade="all, delete-orphan")
    saved_images = db.relationship('SavedImage', backref='user', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.user_id)

    # --- Password Handling ---
    @property
    def password(self):
        """Prevent password from being accessed directly."""
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        """Automatically hashes the password when user.password = 'val' is called."""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Checks the plain text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

class SettingsData(db.Model):
    __tablename__ = 'settings_data'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(20), db.ForeignKey('users.user_id'), nullable=False, unique=True)

    theme = db.Column(db.String(5), default='AUTO')
    
    # Core Persona
    nickname = db.Column(db.String(100), default='Cogni Assistant')
    voice = db.Column(db.String(100), default='Nova')
    language = db.Column(db.String(50), default='English (US)')
    dictation = db.Column(db.Boolean, default=True)
    
    # Strategy
    # This directly controls the generation of the 5 subjects / 25 chapters
    response_length = db.Column(db.String(20), default='balanced') # concise, balanced, detailed
    mode = db.Column(db.String(50), default='Instant')
    
    # Assets
    avatar_path = db.Column(db.String(255), default='static/assets/avatars/default_agent_avatar.png')


class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    issue_type = db.Column(db.String(50), nullable=False)
    issue_details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_resolved = db.Column(db.Boolean, default=False)

    # CHANGE: Set nullable=True so we can keep the review after user is gone
    user_id = db.Column(db.String(20), db.ForeignKey('users.user_id', ondelete="SET NULL"), nullable=True)