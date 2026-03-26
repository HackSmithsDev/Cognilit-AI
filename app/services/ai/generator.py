import os
import json
import time
import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from groq import Groq

from docx import Document
import openpyxl

logger = logging.getLogger(__name__)

# --- NEW: Custom Exception for UI Feedback ---
class UnsupportedFileError(Exception):
    """Exception raised when a file format is not supported by the AI File API."""
    pass

# --- 1. Schema Definitions ---
class ResearchSection(BaseModel):
    header: str
    content: str

class ResearchReport(BaseModel):
    title: str
    summary: str
    sections: List[ResearchSection]
    visual_prompt: str = Field(description="Highly detailed prompt for an image generator representing this research.")

# --- 2. Groq Provider ---
class GroqProvider:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = Groq(api_key=self.api_key)
        self.model_id = "llama-3.3-70b-versatile"

    def generate_structured_report(self, prompt: str, history: List[dict] = None, 
                                   verbosity_instruction: str = "", 
                                   temperature: float = 0.2,
                                   file_path: Optional[str] = None, # Added for signature compatibility
                                   **kwargs) -> ResearchReport:
        
        schema_instruction = """
        Your response must be a valid JSON object with EXACTLY these keys:
        - "title": string
        - "summary": string
        - "sections": list of objects each containing "header" (string) and "content" (string)
        - "visual_prompt": string (highly detailed description)
        """
        
        # Combine system instruction with the user's verbosity/mode settings
        system_content = f"You are a professional research agent. {verbosity_instruction} {schema_instruction}"
        
        messages = [{"role": "system", "content": system_content}]
        
        if history:
            for h in history:
                role = "assistant" if h['role'] == "model" else "user"
                try:
                    text = h['parts'][0]['text']
                except (KeyError, IndexError, TypeError):
                    text = str(h['parts'][0])
                messages.append({"role": role, "content": text})
        
        messages.append({"role": "user", "content": prompt})
        
        completion = self.client.chat.completions.create(
            model=self.model_id,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature # Now dynamic based on Mode
        )

        content = completion.choices[0].message.content
        raw_data = json.loads(content)
        
        if "report" in raw_data: 
            raw_data = raw_data["report"]
            
        return ResearchReport(**raw_data)

# --- 3. Gemini Provider ---
class GeminiProvider:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.client = genai.Client(api_key=self.api_key)
        # Using 2.0 Flash for stable structured output
        self.model_id = "gemini-2.5-flash" 

    def generate_structured_report(self, prompt: str, history: List[dict] = None, 
                                   file_path: Optional[str] = None,
                                   verbosity_instruction: str = "",
                                   temperature: float = 0.3) -> ResearchReport:
        contents = []
        uploaded_file = None 
        if history:
            contents.extend(history)

        try:
            if file_path and os.path.exists(file_path):
                file_ext = file_path.lower()
                
                # Manual Extraction for Office Formats (Workaround for Gemini API limits)
                if file_ext.endswith('.docx'):
                    try:
                        doc = Document(file_path)
                        full_text = '\n'.join([para.text for para in doc.paragraphs])
                        contents.append(f"Context from Word Document:\n{full_text}")
                    except Exception as e:
                        logger.error(f"Word Extraction Error: {e}")

                elif file_ext.endswith('.xlsx'):
                    try:
                        wb = openpyxl.load_workbook(file_path, data_only=True)
                        sheet_data = []
                        for sheet in wb.worksheets:
                            sheet_data.append(f"--- Sheet: {sheet.title} ---")
                            for row in sheet.iter_rows(values_only=True):
                                if any(row):
                                    sheet_data.append(" | ".join([str(cell) if cell is not None else "" for cell in row]))
                        contents.append(f"Context from Excel Spreadsheet:\n" + "\n".join(sheet_data))
                    except Exception as e:
                        logger.error(f"Excel Extraction Error: {e}")

                else:
                    # NATIVE Gemini Upload (PDF/Images)
                    try:
                        uploaded_file = self.client.files.upload(file=file_path)
                        contents.append(uploaded_file)
                        contents.append("Analyze the attached file content to inform the research sections.")
                    except Exception as e:
                        err_str = str(e).upper()
                        if "400" in err_str and "INVALID_ARGUMENT" in err_str:
                            ext = os.path.splitext(file_path)[1].upper() or "Unknown"
                            raise UnsupportedFileError(f"The AI does not support {ext} files. Please use PDF, Word, Excel, or Images.")
                        raise e

            contents.append(f"Research Task: {prompt}")

            # System instruction incorporating User Settings
            sys_inst = f"Synthesize a professional research report. {verbosity_instruction}"

            for attempt in range(3):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_id,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=ResearchReport,
                            temperature=temperature,
                            system_instruction=sys_inst
                        )
                    )
                    if response and response.parsed:
                        return response.parsed
                    raise ValueError("AI returned empty response")
                except Exception as e:
                    if "429" in str(e) and attempt < 2:
                        logger.warning("Quota hit, retrying...")
                        time.sleep(10)
                        continue
                    raise e
        finally:
            if uploaded_file:
                try:
                    self.client.files.delete(name=uploaded_file.name)
                    logger.info(f"Cleaned up file: {uploaded_file.name}")
                except Exception as cleanup_err:
                    logger.error(f"Cleanup failed: {cleanup_err}")