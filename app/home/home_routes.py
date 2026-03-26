from flask import render_template

from . import home_bp


@home_bp.route('/')
def show_login_dialog():
    return render_template('login_dialog.html')

@home_bp.route('/index')
def index():
    # Render the home page template
    return render_template('index.html')