import os

from flask import render_template, jsonify, current_app
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Project, Message, SavedDocument, SavedImage

from . import saved_bp

@saved_bp.route('/')
@login_required
def vault():
    # Fetch projects to show "Organized across X projects" in header
    projects = Project.query.filter_by(user_id=current_user.user_id).all()
    
    # Fetch assets ordered by newest first for the 'Recent' feel
    docs = SavedDocument.query.filter_by(user_id=current_user.user_id)\
        .order_by(SavedDocument.created_at.desc()).all()
        
    images = SavedImage.query.filter_by(user_id=current_user.user_id)\
        .order_by(SavedImage.created_at.desc()).all()
    
    return render_template('saved.html', 
                           projects=projects, 
                           saved_docs=docs, 
                           saved_images=images)

@saved_bp.route('/delete/<string:item_type>/<string:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_type, item_id):
    try:
        model = SavedDocument if item_type == 'doc' else SavedImage
        item = model.query.get_or_404(item_id)

        if item.user_id != current_user.user_id:
            return jsonify({"error": "Unauthorized"}), 403

        # --- SMART FILE CLEANUP ---
        file_path = item.file_path
        
        # Check if any message is still using this file URL
        is_used_in_chat = Message.query.filter_by(file_url=file_path).first()

        if not is_used_in_chat and file_path:
            relative_path = file_path.lstrip('/')
            full_path = os.path.join(current_app.root_path, relative_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        # ---------------------------

        db.session.delete(item)
        db.session.commit()
        
        return jsonify({"status": "success"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Vault Delete Error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500