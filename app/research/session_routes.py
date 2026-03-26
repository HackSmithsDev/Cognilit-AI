import os
from flask import jsonify, render_template, request, current_app, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Project, ChatSession, Message, SavedImage, SavedDocument

from . import api_bp


@api_bp.route('/session/<string:id>')
@login_required
def session(id):
    chat_session = ChatSession.query.filter_by(session_id=id).first_or_404()
    messages = Message.query.filter_by(session_id=id).order_by(Message.timestamp.asc()).all()
    
    return render_template('session.html', 
                           session=chat_session, 
                           messages=messages)


@api_bp.route('/session/add', methods=['POST'])
@login_required
def add_session_to_project():
    data = request.get_json()
    project_id = data.get('project_id')
    session_name = data.get('session_name')

    # 1. Constraint Check: Ensure max 10 subjects per course
    existing_sessions_count = ChatSession.query.filter_by(project_id=project_id).count()
    if existing_sessions_count >= 10:
        return jsonify({
            "status": "error", 
            "message": "Limit reached: Each project can only have 10 subjects."
        }), 400

    # 2. Database Registration Only
    new_session = ChatSession(
        session_name=session_name,
        project_id=project_id
    )
    db.session.add(new_session)
    db.session.commit()

    # 3. Return query to JS - No executor here!
    return jsonify({
        "status": "success",
        "redirect_url": url_for('api.session', id=new_session.session_id),
    }), 200


@api_bp.route('/session/<string:id>/rename', methods=['POST'])
@login_required
def rename_session(id):
    data = request.get_json()
    new_name = data.get('new_name', '').strip()

    # Security check: Session -> Project -> User
    session = ChatSession.query.join(Project).filter(
        ChatSession.session_id == id,
        Project.user_id == current_user.user_id
    ).first_or_404()
    
    session.session_name = new_name
    db.session.commit()
    return jsonify({"status": "success", "new_name": new_name}), 200
    


@api_bp.route('/session/<string:id>/delete', methods=['DELETE'])
@login_required
def delete_session(id):
    # 1. Fetch the session and verify ownership
    session_to_delete = ChatSession.query.join(Project).filter(
        ChatSession.session_id == id,
        Project.user_id == current_user.user_id
    ).first_or_404()

    try:
        # 2. Find all messages in this session that have files
        messages_with_files = Message.query.filter(
            Message.session_id == id, 
            Message.file_url != None
        ).all()

        for msg in messages_with_files:
            # CHECK: Is this file saved in the Vault? 
            # If it's NOT in the vault, we delete the physical file.
            # If it IS in the vault, we keep the file but delete the message record.
            is_in_vault = SavedDocument.query.filter_by(file_path=msg.file_url).first() or \
                          SavedImage.query.filter_by(file_path=msg.file_url).first()

            if not is_in_vault:
                relative_path = msg.file_url.lstrip('/')
                full_path = os.path.join(current_app.root_path, relative_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

        # 3. Delete the Session (SQLAlchemy 'cascade' should handle Messages if configured)
        # If your Model doesn't have cascade delete, delete messages manually first:
        # Message.query.filter_by(session_id=id).delete()
        
        db.session.delete(session_to_delete)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Session and associated files cleared"}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Project Delete Error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500