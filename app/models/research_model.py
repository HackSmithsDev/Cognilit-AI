from app.extensions import db
from datetime import datetime
from .utils import generate_secret_id


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # e.g., "Tax Research" or "Vacation Planning"
    user_id = db.Column(db.String(20), db.ForeignKey('users.user_id'), nullable=False)
    
    # Direct relationship to sessions (skipping the 'chapter' confusion)
    sessions = db.relationship('ChatSession', backref='project', lazy=True, cascade="all, delete-orphan")

class ChatSession(db.Model):
    __tablename__ = 'chat_sessions'
    session_id = db.Column(db.String(20), primary_key=True, default=generate_secret_id)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
    session_name = db.Column(db.String(150), default="New Session")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    messages = db.relationship('Message', backref='session', lazy=True, cascade="all, delete-orphan")

class Message(db.Model):
    __tablename__ = 'messages'
    chat_id = db.Column(db.String(20), primary_key=True, default=generate_secret_id)
    session_id = db.Column(db.String(20), db.ForeignKey('chat_sessions.session_id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False) # 'user' or 'agent'
    message = db.Column(db.Text, nullable=True) # Changed to True so we can send a file with no text
    
    # --- New Fields for Attachments ---
    file_url = db.Column(db.Text, nullable=True) 
    file_type = db.Column(db.String(20), nullable=True) # 'image', 'pdf', 'docx', etc.
    
    # Perfect for Gemini: stores citations/links
    sources = db.Column(db.JSON, nullable=True) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    saved_doc = db.relationship('SavedDocument', backref='original_msg', uselist=False)
    saved_img = db.relationship('SavedImage', backref='original_msg', uselist=False)