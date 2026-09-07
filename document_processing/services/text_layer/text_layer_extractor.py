import fitz
import logging
import string
from typing import Optional, Tuple
from document_processing.schemas.ocr_result import OCRStrategy

logger = logging.getLogger(__name__)

class TextLayerExtractor:
    def extract(self, pdf_path: str, page_number: int) -> Tuple[Optional[str], float, Optional[OCRStrategy]]:
        """
        Extracts text from PDF if a good quality text layer exists.
        Returns: (extracted_text, quality_score, strategy)
        If quality is poor, returns (None, 0.0, None)
        """
        try:
            with fitz.open(pdf_path) as doc:
                page = doc[page_number - 1]
                text = page.get_text("text").strip()
                
                if not text:
                    return None, 0.0, None
                    
                quality_score = self._assess_quality(text)
                
                if quality_score > 0.85:
                    return text, quality_score, OCRStrategy.TEXT_LAYER
                return text, quality_score, None
        except Exception as e:
            logger.error(f"Error extracting text layer from {pdf_path}: {str(e)}")
            return None, 0.0, None
            
    def _assess_quality(self, text: str) -> float:
        char_count = len(text)
        if char_count < 100:
            return 0.0
            
        alpha_count = sum(c.isalpha() for c in text)
        alpha_ratio = alpha_count / max(char_count, 1)
        
        printable_ascii_count = sum(c in string.printable for c in text)
        ascii_ratio = printable_ascii_count / max(char_count, 1)
        
        if alpha_ratio > 0.40 and ascii_ratio > 0.85:
            return 0.99
            
        return 0.5 * alpha_ratio + 0.5 * ascii_ratio
