from fpdf import FPDF
import os
import logging

logger = logging.getLogger(__name__)

class ResearchPDF(FPDF):
    def header(self):
        # Set font for branding
        self.set_font("helvetica", "B", 10)
        self.set_text_color(100, 100, 100) # Slightly darker for readability
        
        # Left Side: System Tag
        self.cell(100, 10, "COGNILIT INTELLIGENCE SYSTEM", align="L")
        
        # Right Side: Report Branding
        self.set_font("helvetica", "I", 9)
        self.cell(0, 10, "AI-Generated Research Report", align="R", ln=True)
        
        # Draw a solid separator line (2px below the text)
        self.set_draw_color(41, 128, 185) # Use your Blue accent color here
        self.set_line_width(0.5)
        self.line(10, 20, 200, 20)
        
        self.ln(10) # Space before the main title starts

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        
        # Add a subtle light grey separator line
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        
        # Set font for footer
        self.set_font("helvetica", "I", 8)
        self.set_text_color(160, 160, 160)
        
        # Left Side: Branding/Copyright
        self.cell(100, 10, "© 2026 CogniLit AI Research Intelligence", align="L")
        
        # Right Side: Page Numbering
        # {nb} is the total page count placeholder
        self.cell(0, 10, f"Page {self.page_no()} of {{nb}}", align="R")

class PDFProvider:
    def create_report(self, report_data, output_path):
        try:
            # Initialize our custom PDF class
            # 'nb' is an alias for total page number
            pdf = ResearchPDF()
            pdf.alias_nb_pages() 
            pdf.set_auto_page_break(auto=True, margin=20)
            pdf.add_page()
            
            # --- Title ---
            pdf.set_font("helvetica", "B", 26)
            pdf.set_text_color(20, 33, 61) # Deep Navy
            pdf.multi_cell(0, 15, report_data.title, align='L')
            pdf.ln(5)
            
            # --- Meta Line ---
            pdf.set_font("helvetica", "B", 9)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f"SUBJECT: {report_data.title.upper()}", ln=True)
            pdf.set_font("helvetica", "", 9)
            pdf.cell(0, 5, f"DATE: 2026-03-07", ln=True)
            pdf.ln(10)
            
            # --- Summary Section ---
            pdf.set_fill_color(240, 240, 240) # Light grey background
            pdf.set_font("helvetica", "B", 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 10, " EXECUTIVE SUMMARY", ln=True, fill=True)
            pdf.ln(2)
            pdf.set_font("times", "", 11) # Serif for better readability in long text
            pdf.multi_cell(0, 6, report_data.summary)
            pdf.ln(10)
            
            # --- Content Sections ---
            for section in report_data.sections:
                # Check for space before adding section to prevent orphaned headers
                if pdf.get_y() > 250:
                    pdf.add_page()

                # Styled Section Header
                pdf.set_font("helvetica", "B", 14)
                pdf.set_text_color(41, 128, 185) # Blue accent
                pdf.cell(0, 10, section.header, ln=True)
                
                # Decorative underline
                pdf.set_draw_color(41, 128, 185)
                pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 30, pdf.get_y())
                pdf.ln(4)
                
                # Section Content
                pdf.set_font("times", "", 11)
                pdf.set_text_color(30, 30, 30)
                pdf.multi_cell(0, 6, section.content)
                pdf.ln(8)
            
            # Ensure folder exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            pdf.output(output_path)
            return True
            
        except Exception as e:
            logger.error(f"PDF Generation Error: {e}")
            return False