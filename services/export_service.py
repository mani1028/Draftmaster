import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document

class ExportService:
    @staticmethod
    def to_pdf(text):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Split by newlines to handle paragraphs roughly
        paragraphs = text.split('\n')
        for p in paragraphs:
            if p.strip():
                story.append(Paragraph(p, styles['Normal']))
                story.append(Spacer(1, 12))
        
        doc.build(story)
        buffer.seek(0)
        return buffer

    @staticmethod
    def to_docx(text):
        doc = Document()
        doc.add_heading('Generated Document', 0)
        
        paragraphs = text.split('\n')
        for p in paragraphs:
            if p.strip():
                doc.add_paragraph(p)
                
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer