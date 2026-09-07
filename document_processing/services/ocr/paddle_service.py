import time
import logging
from typing import Tuple
from paddleocr import PaddleOCR
from document_processing.schemas.ocr_result import OCRStrategy

logger = logging.getLogger(__name__)

class PaddleService:
    def __init__(self, lang='en'):
        # Initialize lazily or pass via dependency injection
        # lang='en' by default, use angle=True to handle rotated images
        self.ocr_engine = PaddleOCR(use_angle_cls=True, lang=lang)

    def extract_text(self, image_path: str) -> Tuple[str, float, int]:
        """
        Returns (extracted_text, confidence, processing_time_ms)
        """
        start_time = time.time()
        try:
            result = self.ocr_engine.ocr(image_path, cls=True)
            
            extracted_text = ""
            total_confidence = 0.0
            word_count = 0
            
            if result and result[0]:
                for line in result[0]:
                    text, confidence = line[1]
                    extracted_text += text + "\n"
                    total_confidence += confidence
                    word_count += 1
            
            avg_confidence = total_confidence / max(word_count, 1)
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return extracted_text.strip(), avg_confidence, processing_time_ms
        except Exception as e:
            logger.error(f"PaddleOCR error on {image_path}: {str(e)}")
            return "", 0.0, int((time.time() - start_time) * 1000)
