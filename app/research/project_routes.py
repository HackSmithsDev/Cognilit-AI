import os
from flask import abort, jsonify, render_template, request, current_app, url_for
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Project, ChatSession, Message, SavedImage, SavedDocument

from . import api_bp


@api_bp.route('/project/<int:id>')
@login_required
def project_view(id):
    project = Project.query.get_or_404(id)
    
    # Security: Ensure the project belongs to the current user
    if project.user_id != current_user.user_id:
        abort(403)

    # Sort sessions by most recent
    sessions = sorted(project.sessions, key=lambda x: x.created_at, reverse=True)
    
    return render_template('dashboard.html', 
                           project=project, 
                           sessions=sessions)


@api_bp.route('/project/new', methods=['POST'])
@login_required
def create_project_session():
    data = request.get_json() 
    project_name = data.get('project_name')
    session_name = data.get('session_name')

    # 1. Database Registration Only
    new_project = Project(name=project_name, user_id=current_user.user_id)
    db.session.add(new_project)
    db.session.flush() 

    new_session = ChatSession(
        session_name=session_name,
        project_id=new_project.id
    )
    db.session.add(new_session)
    db.session.commit() 

    # 2. Return query to JS - No executor here!
    return jsonify({
        "status": "success",
        "redirect_url": url_for('api.session', id=new_session.session_id),
    }), 200

@api_bp.route('/project/<int:id>/rename', methods=['POST'])
@login_required
def rename_project(id):
    data = request.get_json()
    new_name = data.get('new_name', '').strip()

    if not new_name:
        return jsonify({"status": "error", "message": "Project name cannot be empty."}), 400

    project = Project.query.filter_by(id=id, user_id=current_user.user_id).first_or_404()
    
    try:
        project.name = new_name
        db.session.commit()
        return jsonify({"status": "success", "new_name": new_name}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    

@api_bp.route('/project/<int:id>/delete', methods=['DELETE'])
@login_required
def delete_project(id):
    # 1. Fetch project and verify ownership
    project = Project.query.filter_by(id=id, user_id=current_user.user_id).first_or_404()
    
    try:
        # 2. Get all sessions belonging to this project
        sessions = ChatSession.query.filter_by(project_id=id).all()
        
        for session in sessions:
            # 3. Find messages with files within each session
            messages_with_files = Message.query.filter(
                Message.session_id == session.session_id, 
                Message.file_url != None
            ).all()

            for msg in messages_with_files:
                # Security Check: Only delete if not saved in Vault
                is_in_vault = SavedDocument.query.filter_by(file_path=msg.file_url).first() or \
                              SavedImage.query.filter_by(file_path=msg.file_url).first()

                if not is_in_vault:
                    relative_path = msg.file_url.lstrip('/')
                    full_path = os.path.join(current_app.root_path, relative_path)
                    
                    if os.path.exists(full_path):
                        os.remove(full_path)

        # 4. Delete the project (assuming cascade delete is set in models)
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({"status": "success", "message": "Project and all session data cleared"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Project Delete Error: {str(e)}")
        return jsonify({"status": "error", "message": "Failed to delete project data"}), 500
    