import os
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

from app.extensions import db, limiter
from app.models import Message, SavedImage, SavedDocument

from app.services.ai import ResearchOrchestrator, UnsupportedFileError

from . import api_bp


@api_bp.route('/session/<string:session_id>/send', methods=['POST'])
@login_required
@limiter.limit("10 per 5 minutes")
def send_message(session_id):
    user_text = request.form.get('message', '').strip()
    uploaded_file = request.files.get('file')
    client_generated_id = request.form.get('chat_id') 
    gen_type = request.form.get('generation_type')

    if not user_text and not uploaded_file:
        return jsonify({"status": "error", "message": "No content provided"}), 400

    try:
        file_url = None
        file_ext = None
        save_path = None # This is what we pass to Gemini
        
        # 1. Handle File Uploads
        if uploaded_file and uploaded_file.filename != '':
            filename = secure_filename(uploaded_file.filename)
            file_ext = filename.split('.')[-1].lower()
            subfolder = 'images' if file_ext in ['jpg', 'jpeg', 'png', 'webp'] else 'documents'
            
            # Use os.path.join for cross-platform (Mac/Windows) safety
            upload_base = current_app.config['UPLOAD_FOLDER']
            dest_folder = os.path.join(upload_base, subfolder)
            os.makedirs(dest_folder, exist_ok=True)
            
            unique_name = f"{session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            save_path = os.path.join(dest_folder, unique_name)
            uploaded_file.save(save_path)
            file_url = f"/static/uploads/{subfolder}/{unique_name}"

        # 2. Save User Message
        user_msg = Message(
            chat_id=client_generated_id,
            session_id=session_id,
            sender='user',
            message=user_text or "[Attached File]", # Fallback if message is empty
            file_url=file_url,
            file_type=file_ext
        )
        db.session.add(user_msg)
        
        # 3. Synchronous AI Integration
        orchestrator = ResearchOrchestrator()
        
        # If user_text is empty but we have a file, give Gemini a default prompt
        ai_prompt = user_text if user_text else "Please analyze the attached file."

        ai_result = orchestrator.handle_research_sync(
            app=current_app._get_current_object(),
            session_id=session_id, 
            user_text=ai_prompt, 
            gen_type=gen_type,
            file_path=save_path # <--- Gemini now 'sees' the file
        )
        
        # 4. Save AI Response Message
        ai_msg = Message(
            session_id=session_id,
            sender='agent',
            message=ai_result.get('message'),
            file_url=ai_result.get('file_url'),
            file_type=ai_result.get('file_type'),
        )
        db.session.add(ai_msg)
        db.session.commit()

        return jsonify({
            "status": "success",
            "ai_message": ai_msg.message,
            "ai_chat_id": ai_msg.chat_id,
            "ai_file_url": ai_msg.file_url,
            "ai_file_type": ai_msg.file_type,
            "timestamp": ai_msg.timestamp.strftime('%I:%M %p')
        }), 200

    except UnsupportedFileError as ufe:
        # Catch our custom error from generator.py
        return jsonify({"status": "error", "message": str(ufe)}), 400
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error: {str(e)}")
        return jsonify({"status": "error", "message": "I couldn't process that right now."}), 500


@api_bp.route('/message/<string:chat_id>/save', methods=['POST'])
@login_required
def save_to_vault(chat_id):
    msg = Message.query.get_or_404(chat_id)
    
    # Pre-check: Prevent duplicate saves (Safety first!)
    if msg.saved_doc or msg.saved_img:
        return jsonify({"status": "error", "message": "Already saved to vault"}), 400
    
    try:
        if msg.file_type in ['jpg', 'jpeg', 'png', 'webp', 'gif']:
            # Promote to SavedImage
            new_save = SavedImage(
                user_id=current_user.user_id,
                session_id=msg.session_id,
                message_id=msg.chat_id, # Link established here
                title=f"Ref: {msg.session.project.name} | {msg.session.session_name}",
                file_path=msg.file_url,
                file_type=msg.file_type
            )
        else:
            # Promote to SavedDocument
            new_save = SavedDocument(
                user_id=current_user.user_id,
                session_id=msg.session_id,
                message_id=msg.chat_id, # Link established here
                title=f"Study: {msg.session.project.name} | {msg.session.session_name}",
                file_path=msg.file_url,
                file_type=msg.file_type
            )
        
        db.session.add(new_save)
        db.session.commit()
        return jsonify({"status": "success", "message": "Promoted to Vault"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
