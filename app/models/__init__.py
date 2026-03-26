from .user_model import User, SettingsData, Reviews
from .research_model import Project, ChatSession, Message
from .saved_model import SavedDocument, SavedImage

# This allows you to import everything from app.models directly
__all__ = [
    'User', 
    'SettingsData', 
    'Reviews',
    'Project', 
    'ChatSession', 
    'Message', 
    'SavedDocument', 
    'SavedImage'
]