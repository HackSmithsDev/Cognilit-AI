import os

from flask import current_app, render_template, request, jsonify, url_for
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import SettingsData

from . import setting_bp


@setting_bp.route('/', methods=['GET'])
@login_required
def settings():
    settings_data = current_user.settings_data
    if not settings_data:
        settings_data = SettingsData(user_id=current_user.user_id)
        db.session.add(settings_data)
        db.session.commit()

    return render_template('settings.html', settings=settings_data)


@setting_bp.route('/update-theme', methods=['POST'])
@login_required
def update_theme():
    data = request.get_json()
    theme = data.get('theme') # Expecting 'Light' or 'Dark'
    
    try:
        # Check if settings_data exists for user, create if not
        if not current_user.settings_data:
            new_settings = SettingsData(user_id=current_user.user_id, theme=theme)
            db.session.add(new_settings)
        else:
            current_user.settings_data.theme = theme
        
        db.session.commit()
        return jsonify({'status': 'success', 'theme': theme})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Theme change error: {e}')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@setting_bp.route('/update-agent-avatar', methods=['POST'])
@login_required
def update_agent_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 1. Handle Extensions and Filenames
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        return jsonify({'error': 'Invalid file type'}), 400
        
    filename = secure_filename(f"agent_{current_user.user_id}{ext}")
    
    # 2. Path Management
    # DB path (what the browser sees)
    db_rel_path = f"static/uploads/agent_avatars/{filename}"
    
    # OS path (where the server actually writes the file)
    # This assumes UPLOAD_FOLDER points to 'app/static/uploads'
    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'agent_avatars', filename)

    # 3. Cleanup Old Avatar
    old_path = current_user.settings_data.avatar_path
    if old_path and 'default_agent_avatar.png' not in old_path:
        # Construct absolute path to delete the old file
        old_abs_path = os.path.join(current_app.root_path, old_path)
        if os.path.exists(old_abs_path):
            os.remove(old_abs_path)
    
    # 4. Save and Commit
    try:
        file.save(abs_path)
        
        current_user.settings_data.avatar_path = db_rel_path
        db.session.commit()
        
        return jsonify({'message': 'Success', 'path': db_rel_path})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Save failed: {str(e)}'}), 500

@setting_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    settings = current_user.settings_data
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400

    # List of allowed fields that match your SettingsData model columns
    # This prevents users from accidentally trying to update sensitive fields
    allowed_fields = [
        'nickname', 
        'voice', 
        'language', 
        'dictation',
        'response_length', 
        'mode'
    ]

    # Dynamically update only the fields sent in the request
    for key, value in data.items():
        if key in allowed_fields:
            setattr(settings, key, value)
    
    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Settings updated"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    
