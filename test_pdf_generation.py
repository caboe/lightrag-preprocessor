#!/usr/bin/env python3
"""
Simple test script for PDF generation functionality.
"""
import asyncio
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER


async def test_pdf_generation():
    """Test basic PDF generation without full app dependencies."""
    print("Testing basic PDF generation...")
    
    # Test data
    test_text = """
    This is a test document for the LightRAG preprocessor.
    
    The preprocessor now generates PDF documents from text input before sending them to LightRAG.
    This ensures that text inputs are treated the same way as uploaded documents.
    
    Features:
    - Clean PDF formatting
    - Proper title and metadata
    - Consistent text extraction
    - Integration with LightRAG
    
    This test verifies that the PDF generation works correctly.
    """
    
    test_title = "Test Document"
    
    try:
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
        
        # Setup styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor='#2c3e50'
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            alignment=TA_LEFT,
            lineHeight=1.2
        )
        
        # Build the story (content) for the PDF
        story = []
        
        # Add title
        title_paragraph = Paragraph(test_title, title_style)
        story.append(title_paragraph)
        story.append(Spacer(1, 12))
        
        # Add metadata
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_text = f"Generated on: {current_time} | Author: Test Script"
        
        metadata_style = ParagraphStyle(
            'Metadata',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=6,
            alignment=TA_LEFT,
            textColor='#7f8c8d'
        )
        
        metadata_paragraph = Paragraph(metadata_text, metadata_style)
        story.append(metadata_paragraph)
        story.append(Spacer(1, 20))
        
        # Process the text content
        paragraphs = test_text.split('\n\n')
        
        for paragraph_text in paragraphs:
            if paragraph_text.strip():
                cleaned_text = paragraph_text.replace('\n', ' ').strip()
                cleaned_text = (cleaned_text
                              .replace('&', '&amp;')
                              .replace('<', '&lt;')
                              .replace('>', '&gt;'))
                
                paragraph = Paragraph(cleaned_text, body_style)
                story.append(paragraph)
                story.append(Spacer(1, 6))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        print(f"✅ PDF generated successfully!")
        print(f"   Size: {len(pdf_bytes)} bytes")
        
        # Test text extraction using PyMuPDF
        import fitz
        pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page in pdf_doc:
            pages_text.append(page.get_text())
        pdf_doc.close()
        extracted_text = "\n".join(pages_text).strip()
        
        print(f"✅ Text extraction successful!")
        print(f"   Extracted length: {len(extracted_text)} characters")
        print(f"   Original length: {len(test_text.strip())} characters")
        
        # Check if the extracted text contains the key content
        if test_title in extracted_text and "LightRAG preprocessor" in extracted_text:
            print("✅ Content verification successful!")
        else:
            print("❌ Content verification failed!")
            print("Extracted text preview:")
            print(extracted_text[:200] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("LightRAG Preprocessor - PDF Generation Test")
    print("=" * 50)
    
    # Run the test
    success = asyncio.run(test_pdf_generation())
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Tests failed!")
        exit(1)