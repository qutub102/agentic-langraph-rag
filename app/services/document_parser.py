"""PDF parsing and text extraction."""
import base64
from typing import Optional

import fitz  # PyMuPDF

from app.utils.logging import log_error, logger


class DocumentParser:
    """PDF document parser."""
    
    @staticmethod
    def parse_pdf(file_content_base64: str) -> Optional[str]:
        """
        Parse PDF from base64 content and extract text.
        
        Args:
            file_content_base64: Base64 encoded PDF content
            
        Returns:
            Extracted text content or None if parsing fails
        """
        try:
            # Decode base64
            pdf_bytes = base64.b64decode(file_content_base64)
            
            # Parse PDF with PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(len(doc)):
                try:
                    page = doc[page_num]
                    # Get text blocks sorted roughly by reading order
                    text = page.get_text()
                    if text and text.strip():
                        text_parts.append(text.strip())
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {str(e)}")
                    continue
            
            if not text_parts:
                logger.warning("No text extracted from PDF. This might be a scanned or image-only PDF.")
                return "[The uploaded document did not contain any extractable text. It might be an image-only or scanned PDF without an OCR text layer.]"
            
            full_text = "\n\n".join(text_parts)
            logger.info(f"Successfully parsed PDF: {len(full_text)} characters extracted")
            return full_text
            
        except Exception as e:
            log_error(e, {"context": "PDF parsing"})
            return None
