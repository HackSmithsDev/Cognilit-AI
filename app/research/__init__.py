from flask import Blueprint

api_bp = Blueprint(
    'api',
    __name__,
    template_folder='templates',
    static_folder='static',
)

from . import project_routes, session_routes, chat_routes