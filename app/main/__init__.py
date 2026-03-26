from flask import Blueprint

user_bp = Blueprint(
    'user',
    __name__,
)

setting_bp = Blueprint(
    'setting',
    __name__,
    template_folder='templates',
    static_folder='static',
)

saved_bp = Blueprint(
    'saved',
    __name__,
    template_folder='templates',
    static_folder='static',
)

from . import user_routes, setting_routes, saved_routes