"""
PDF generation service for converting text to PDF documents.
"""
import io
import tempfile
from typing import Optional, Tuple
from datetime import datetime
import structlog
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER

logger = structlog.get_logger(__name__)


class PDFGenerationService:
    """Service for generating PDF documents from text content."""
    
    def __init__(self):
        """Initialize PDF generation service."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles for PDF generation."""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='#2c3e50'
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT,
            leftIndent=0,
            rightIndent=0,
            lineHeight=1.2
        )
        
        # Metadata style
        self.metadata_style = ParagraphStyle(
            'Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor='#7f8c8d'
        )
    
    async def generate_pdf_from_text(
        self, 
        text: str, 
        title: Optional[str] = None,
        author: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """
        Generate a PDF document from text content.
        
        Args:
            text: The text content to convert to PDF
            title: Optional title for the document
            author: Optional author name
            
        Returns:
            Tuple of (PDF bytes, filename)
            
        Raises:
            Exception: If PDF generation fails
        """
        try:
            logger.info("Generating PDF from text", 
                       text_length=len(text), 
                       title=title)
            
            # Create a BytesIO buffer to store the PDF
            buffer = io.BytesIO()
            
            # Create the PDF document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build the story (content) for the PDF
            story = []
            
            # Add title if provided
            if title:
                title_paragraph = Paragraph(title, self.title_style)
                story.append(title_paragraph)
                story.append(Spacer(1, 12))
            
            # Add metadata
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            metadata_text = f"Generated on: {current_time}"
            if author:
                metadata_text += f" | Author: {author}"
            
            metadata_paragraph = Paragraph(metadata_text, self.metadata_style)
            story.append(metadata_paragraph)
            story.append(Spacer(1, 20))
            
            # Process the text content
            # Split text into paragraphs and handle line breaks
            paragraphs = text.split('\n\n')
            
            for paragraph_text in paragraphs:
                if paragraph_text.strip():
                    # Replace single line breaks with spaces, but preserve intentional formatting
                    cleaned_text = paragraph_text.replace('\n', ' ').strip()
                    
                    # Escape HTML characters for ReportLab
                    cleaned_text = (cleaned_text
                                  .replace('&', '&amp;')
                                  .replace('<', '&lt;')
                                  .replace('>', '&gt;'))
                    
                    paragraph = Paragraph(cleaned_text, self.body_style)
                    story.append(paragraph)
                    story.append(Spacer(1, 6))
            
            # Build the PDF
            doc.build(story)
            
            # Get the PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            # Generate filename
            safe_title = self._sanitize_filename(title) if title else "text_document"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_title}_{timestamp}.pdf"
            
            logger.info("PDF generated successfully", 
                       filename=filename,
                       pdf_size=len(pdf_bytes))
            
            return pdf_bytes, filename
            
        except Exception as e:
            logger.error("Failed to generate PDF", error=str(e))
            raise Exception(f"PDF generation failed: {str(e)}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename by removing invalid characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename safe for filesystem
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove extra spaces and limit length
        sanitized = '_'.join(sanitized.split())
        sanitized = sanitized[:50]  # Limit to 50 characters
        
        return sanitized if sanitized else "document"
    
    async def save_pdf_to_temp(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Save PDF bytes to a temporary file.
        
        Args:
            pdf_bytes: PDF content as bytes
            filename: Desired filename
            
        Returns:
            Path to the temporary file
            
        Raises:
            Exception: If saving fails
        """
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.pdf',
                prefix='generated_'
            )
            
            # Write PDF bytes to the file
            temp_file.write(pdf_bytes)
            temp_file.close()
            
            logger.info("PDF saved to temporary file", 
                       temp_path=temp_file.name,
                       filename=filename)
            
            return temp_file.name
            
        except Exception as e:
            logger.error("Failed to save PDF to temp file", error=str(e))
            raise Exception(f"Failed to save PDF: {str(e)}")


# Global service instance
pdf_service = PDFGenerationService()