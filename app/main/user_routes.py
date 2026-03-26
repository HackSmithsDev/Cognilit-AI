import os

from flask import current_app, request, jsonify, url_for, redirect
from flask_login import login_required, current_user, logout_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Reviews

from app.services.email import send_support_assurance_email, send_account_deletion_email

from . import user_bp

@user_bp.route('/update-user-avatar', methods=['POST'])
@login_required
def update_user_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # 1. Secure the filename and create path
    # We use user_id to keep filenames unique
    ext = os.path.splitext(file.filename)[1]
    filename = secure_filename(f"avatar_user_{current_user.user_id}{ext}")

    if current_user.profile_pic and current_user.profile_pic != 'static/assets/avatars/default_profile_pic.png':
        os.remove(os.path.join(current_app.config['BASE_DIR'], 'app', current_user.profile_pic))
    
    # Relative path for the DB, absolute path for saving
    rel_path = f"static/uploads/user_avatars/{filename}"
    abs_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'user_avatars', filename)

    # 2. Save the file
    file.save(abs_path)

    # 3. Update Database
    current_user.profile_pic = rel_path
    db.session.commit()

    return jsonify({'message': 'Success', 'path': rel_path})


@user_bp.route('/update-details', methods=['POST'])
@login_required
def update_details():
    try:
        # Update current_user directly using your model's field names
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.age = int(request.form.get('age'))
        current_user.gender = request.form.get('gender')
        current_user.profession = request.form.get('profession')

        db.session.commit()
        return jsonify({"status": "success", "message": "Profile synced!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    old_p = request.form.get('old_password')
    new_p = request.form.get('new_password')

    # Use the method you defined in your User model
    if not current_user.verify_password(old_p):
        return jsonify({"status": "error", "message": "Current password is wrong"}), 400

    try:
        # Your @password.setter hashes this automatically!
        current_user.password = new_p 
        db.session.commit()
        return jsonify({"status": "success", "message": "Security updated"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Update failed"}), 500



@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user() # flask-login handles clearing the session
    
    # Check if the request expects JSON (like from a fetch call)
    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            "status": "success", 
            "redirect": url_for('home.index')
        })
    
    # Fallback for standard form submissions
    return redirect(url_for('home.index'))


@user_bp.route('/support-ticket', methods=['POST'])
@login_required
def support_ticket():
    data = request.get_json()
    issue_type = data.get('issue_type')
    details = data.get('details') # This comes from your JS JSON payload
    
    if not issue_type or not details:
        return jsonify({"status": "error", "message": "Please provide all details."}), 400
    
    try:
        # Match the model column names exactly: issue_details and user_id
        review = Reviews(
            user_id = current_user.user_id,
            issue_type = issue_type,
            issue_details = details
        )
        db.session.add(review)
        db.session.commit()

        # Trigger the async email logic
        send_support_assurance_email(current_user, issue_type, details)

        return jsonify({"status": "success", "message": "Issue reported successfully!"}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Help Center database error: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

@user_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account():
    # 1. Capture info and objects before session detachment
    user_id = current_user.user_id
    user_email = current_user.email
    user_name = current_user.first_name
    user_obj = current_user 

    # 2. Gather all physical file paths to be deleted
    # We collect them into a list first to ensure we have the paths before DB deletion
    files_to_delete = []

    # A. Agent Avatar (from SettingsData)
    if user_obj.settings_data and 'default_agent_avatar.png' not in user_obj.settings_data.avatar_path:
        files_to_delete.append(user_obj.settings_data.avatar_path)

    # B. Saved Documents (PDFs/Docx from 25-chapter research)
    for doc in user_obj.saved_documents:
        files_to_delete.append(doc.file_path)

    # C. Saved Images (DALL-E/Gemini generated assets)
    for img in user_obj.saved_images:
        files_to_delete.append(img.file_path)

    # D. Profile Picture (User's own upload)
    if 'default_profile_pic.png' not in user_obj.profile_pic:
        files_to_delete.append(user_obj.profile_pic)

    # E Images/Documents not saved but exists in messages
    for proj in user_obj.projects:
        for sesn in proj.sessions:
            for msg in sesn.messages:
                if msg.file_url:
                    files_to_delete.append(msg.file_url)
    print(files_to_delete)

    try:
        # 3. Physical File Deletion
        for relative_path in files_to_delete:
            if relative_path and isinstance(relative_path, str):
                # Standardize: remove any accidental leading slash
                clean_rel_path = relative_path.lstrip('/')
                
                # Resolve to the absolute path using the app root
                abs_path = os.path.normpath(os.path.join(current_app.root_path, clean_rel_path))
                
                if os.path.exists(abs_path):
                    try:
                        os.remove(abs_path)
                        current_app.logger.info(f"Successfully wiped: {abs_path}")
                    except Exception as e:
                        current_app.logger.error(f"Permission error deleting {abs_path}: {e}")
                else:
                    current_app.logger.warning(f"File not found during wipeout: {abs_path}")

        # 4. Database Deletion
        db.session.delete(user_obj)
        db.session.commit()
        
        # 5. Session Cleanup
        logout_user()

        # 6. Final Notification (Async)
        send_account_deletion_email(user_email, user_name)

        return jsonify({
            "status": "success", 
            "message": "All data, images, and documents have been permanently wiped.", 
            "redirect": url_for('home.index')
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Critical wipeout failure for {user_id}: {e}")
        return jsonify({"status": "error", "message": "Wipeout failed. Please contact admin."}), 500
