from app.extensions import db
from datetime import datetime, timezone
from .utils import generate_secret_id

class SavedDocument(db.Model):
    __tablename__ = 'saved_documents'

    id = db.Column(db.String(20), primary_key=True, default=generate_secret_id)
    user_id = db.Column(db.String(20), db.ForeignKey('users.user_id'), nullable=False)
    session_id = db.Column(db.String(20), db.ForeignKey('chat_sessions.session_id', ondelete="SET NULL"), nullable=True)
    message_id = db.Column(db.String(20), db.ForeignKey('messages.chat_id', ondelete="SET NULL"), nullable=True)
    
    title = db.Column(db.String(255), nullable=False)

    file_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class SavedImage(db.Model):
    __tablename__ = 'saved_images'

    id = db.Column(db.String(20), primary_key=True, default=generate_secret_id)
    user_id = db.Column(db.String(20), db.ForeignKey('users.user_id'), nullable=False)
    session_id = db.Column(db.String(20), db.ForeignKey('chat_sessions.session_id', ondelete="SET NULL"), nullable=True)
    message_id = db.Column(db.String(20), db.ForeignKey('messages.chat_id', ondelete="SET NULL"), nullable=True)
    
    title = db.Column(db.String(255), nullable=False)
    # Professional path storage: static/uploads/images/filename.png
    file_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.Text, nullable=False) 
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))