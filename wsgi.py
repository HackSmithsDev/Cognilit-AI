import os
from app import create_app

# Set FLASK_CONFIG environment variable if needed (default is 'development')
config_name = os.environ.get('FLASK_CONFIG') or 'default'
app = create_app(config_name)

if __name__ == '__main__':
    # Flask app will run on host 0.0.0.0 and port 5000 by default
    app.debug = app.config['DEBUG']
    app.run(host=os.getenv('FLASK_HOST'), port=os.getenv('FLASK_RUN_PORT'))