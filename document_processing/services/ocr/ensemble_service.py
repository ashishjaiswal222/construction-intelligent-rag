import time
import logging
from typing import Tuple
from .paddle_service import PaddleService
from .gemini_vision_service import GeminiVisionService

logger = logging.getLogger(__name__)

class EnsembleService:
    def __init__(self, paddle_svc: PaddleService, gemini_svc: GeminiVisionService):
        self.paddle_svc = paddle_svc
        self.gemini_svc = gemini_svc

    def extract_text(self, image_path: str) -> Tuple[str, float, int]:
        """
        Runs PaddleOCR first. If confidence is below 0.78, escalates to Gemini.
        Returns (text, confidence, processing_time)
        """
        start_time = time.time()
        
        text, conf, p_time = self.paddle_svc.extract_text(image_path)
        
        if conf < 0.78:
            logger.info(f"PaddleOCR confidence {conf:.2f} < 0.78. Escalating to Gemini Vision.")
            g_text, g_conf, g_time = self.gemini_svc.extract_text(image_path)
            
            # Use Gemini result if it returned something
            if g_text:
                total_time = int((time.time() - start_time) * 1000)
                return g_text, g_conf, total_time
                
        total_time = int((time.time() - start_time) * 1000)
        return text, conf, total_time
