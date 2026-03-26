from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_executor import Executor
from flask_migrate import Migrate

# Initialize the extensions
login_manager = LoginManager()
db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)
mail = Mail()
executor = Executor()
migrate = Migrate()