import time
import json
import logging
import google.generativeai as genai
from typing import Tuple, List
from django.conf import settings
from document_processing.utils.image_utils import encode_image_to_base64
from document_processing.prompts.handwriting_prompt import HANDWRITING_EXTRACTION_PROMPT

logger = logging.getLogger(__name__)

class GeminiVisionService:
    def __init__(self):
        import os
        import random
        
        # Support API Key Rotation
        keys_str = os.environ.get('GEMINI_API_KEYS', '') or os.environ.get('GOOGLE_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        keys = [k.strip() for k in keys_str.split(',') if k.strip()]
        
        if keys:
            selected_key = random.choice(keys)
            genai.configure(api_key=selected_key)
            
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def extract_text(self, image_path: str) -> Tuple[str, float, int]:
        start_time = time.time()
        try:
            # Upload file or use base64
            # For simplicity, using genai.upload_file or just passing PIL Image
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            prompt = "Extract all text from this image exactly as it appears. Preserve the layout as much as possible."
            response = self.model.generate_content([prompt, img])
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            # Gemini doesn't provide per-word confidence, estimate 0.95 if success
            return response.text.strip(), 0.95, processing_time_ms
        except Exception as e:
            logger.error(f"Gemini Vision error on {image_path}: {str(e)}")
            return "", 0.0, int((time.time() - start_time) * 1000)

    def extract_handwriting(self, image_path: str) -> Tuple[List[str], float, int]:
        start_time = time.time()
        try:
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            response = self.model.generate_content([HANDWRITING_EXTRACTION_PROMPT, img])
            text_response = response.text
            
            # Clean up markdown fences if present
            if text_response.startswith('```json'):
                text_response = text_response[7:-3].strip()
            elif text_response.startswith('```'):
                text_response = text_response[3:-3].strip()
                
            segments = json.loads(text_response)
            if not isinstance(segments, list):
                segments = []
                
            processing_time_ms = int((time.time() - start_time) * 1000)
            return segments, 0.90, processing_time_ms
        except Exception as e:
            logger.error(f"Gemini Handwriting error on {image_path}: {str(e)}")
            return [], 0.0, int((time.time() - start_time) * 1000)
