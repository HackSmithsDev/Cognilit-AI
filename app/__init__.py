import redis
import re
from flask import Flask, request, jsonify, flash, redirect, url_for
from flask_login import current_user
from sqlalchemy.orm import joinedload

# 1. Extensions (Removed 'mail')
from .extensions import db, login_manager, limiter, executor, migrate

# --- Mock Redis Class ---
class FakeRedis:
    def __init__(self): self._storage = {}
    def get(self, key): return self._storage.get(key)
    def set(self, key, value, ex=None): self._storage[key] = str(value) 
    def delete(self, key): self._storage.pop(key, None)
    def ping(self): return True

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # 2. Configuration
    from config import config_by_name, Config
    config_class = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_class)
    Config.init_app(app)

    # 3. Initialize Extensions
    app.config.setdefault('RATELIMIT_STORAGE_URI', app.config.get('REDIS_URL', 'memory://'))
    
    db.init_app(app)
    executor.init_app(app)
    limiter.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    login_manager.session_protection = "strong"
    login_manager.login_view = 'home.show_login_dialog'
    login_manager.login_message_category = "info"

    # 4. Redis Integration
    try:
        app.redis = redis.from_url(app.config['REDIS_URL'], decode_responses=True)
        app.redis.ping()
    except Exception as e:
        app.logger.warning(f"!!! Redis failed ({e}). Initializing FakeRedis fallback !!!")
        app.redis = FakeRedis()

    # 5. Blueprint Registration
    from .home import home_bp
    from .admin import admin_bp
    from .auth import auth_bp
    from .research import api_bp
    from .main import user_bp, setting_bp, saved_bp

    app.register_blueprint(home_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(setting_bp, url_prefix='/setting')
    app.register_blueprint(saved_bp, url_prefix='/vault')

    # 6. User Loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(user_id)

    # 7. Application Context Block
    with app.app_context():
        from . import models

        if config_name == 'development':
            db.create_all()

        from flask_limiter import RateLimitExceeded
        @app.errorhandler(RateLimitExceeded)
        def handle_ratelimit_error(e):
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Too many requests."}), 429
            flash("You're moving too fast! Please wait a moment.", "danger")
            return redirect(url_for('home.show_login_dialog'))

    # 8. Global Context Processor
    @app.context_processor
    def inject_sidebar_data():
        if not current_user.is_authenticated:
            return dict(all_projects=[])
        try:
            from app.models import Project
            projects = Project.query.filter_by(user_id=current_user.user_id)\
                .options(joinedload(Project.sessions)).all()
        except Exception as e:
            app.logger.error(f"Sidebar injection failed: {e}")
            projects = []
        return dict(all_projects=projects)

    return app