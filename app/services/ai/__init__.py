import os
from datetime import datetime
from app.models import Message, SettingsData

from .generator import GeminiProvider, GroqProvider, UnsupportedFileError
from .image_gen import ImageProvider
from .pdf_engine import PDFProvider

class ResearchOrchestrator:
    def __init__(self):
        self.gemini = GeminiProvider()
        self.groq = GroqProvider()
        self.img = ImageProvider()
        self.pdf = PDFProvider()

    def _get_history(self, session_id):
        """Fetches and formats history for Gemini/Groq SDKs."""
        messages = Message.query.filter_by(session_id=session_id)\
            .order_by(Message.timestamp.desc())\
            .limit(10).all()
        
        formatted_history = []
        for msg in reversed(messages):
            role = "user" if msg.sender == 'user' else "model"
            text_content = msg.message if msg.message else "[Attached File]"
            formatted_history.append({"role": role, "parts": [{"text": text_content}]})
        
        return formatted_history

    def handle_research_sync(self, app, session_id, user_text, gen_type, file_path=None, user_id=None):
        try:
            # 1. Fetch User Settings
            user_settings = SettingsData.query.filter_by(user_id=user_id).first()
            verbosity = user_settings.response_length if user_settings else 'balanced'
            op_mode = user_settings.mode if user_settings else 'Instant'
            
            # 2. Map Mode to Instructions & Temperature
            if op_mode == 'Deep':
                mode_instruction = "Use a 'Chain of Thought' approach for deep analytical synthesis."
                target_temp = 0.4 
            else:
                mode_instruction = "Focus on speed and immediate clarity."
                target_temp = 0.1 
            
            verbosity_map = {
                'concise': "Keep research summaries brief.",
                'balanced': "Provide standard research depth.",
                'detailed': "Provide an exhaustive deep-dive."
            }
            custom_instruction = f"{mode_instruction} {verbosity_map.get(verbosity, '')}"

            # 3. Context Preparation
            upload_folder = app.config['UPLOAD_FOLDER']
            history = self._get_history(session_id)
            has_file = file_path and os.path.exists(file_path)
            
            # 4. Provider Selection (Gemini for files, Groq for speed)
            provider = self.gemini if has_file else self.groq

            # 5. Handle Image Generation Specifically
            if gen_type == 'image':
                # Use Groq to expand the prompt regardless of file presence
                img_struct = self.groq.generate_structured_report(
                    user_text, 
                    history=history,
                    verbosity_instruction="Create a detailed visual prompt."
                )
                
                # FIXED: Using positional arguments to match ImageProvider.generate signature
                local_file_url = self.img.generate(
                    session_id, 
                    img_struct.visual_prompt, 
                    user_text, 
                    upload_folder
                )
                
                return {
                    "message": "Generated a visual representation based on our session content.",
                    "file_url": local_file_url,
                    "file_type": "png"
                }

            # 6. Unified Call for Chat and PDF
            report_data = provider.generate_structured_report(
                prompt=user_text, 
                history=history, 
                file_path=file_path if has_file else None, 
                verbosity_instruction=custom_instruction,
                temperature=target_temp
            )

            if gen_type == 'pdf':
                filename = f"report_{session_id}_{datetime.now().strftime('%H%M%S')}.pdf"
                relative_path = f"documents/{filename}"
                full_path = os.path.join(upload_folder, relative_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                self.pdf.create_report(report_data, full_path)
                
                return {
                    "message": f"### {report_data.title}\n\n{report_data.summary}",
                    "file_url": f"/static/uploads/{relative_path}",
                    "file_type": "pdf"
                }

            # Standard Chat Response
            return {
                "message": report_data.summary,
                "file_url": None,
                "file_type": None
            }

        except UnsupportedFileError as ufe:
            raise ufe
        except Exception as e:
            app.logger.error(f"Hybrid Sync AI Error: {e}")
            return {
                "message": "The research intelligence system is currently recalibrating. Please try again.", 
                "file_url": None
            }