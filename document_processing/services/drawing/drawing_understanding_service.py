import json
import logging
import google.generativeai as genai
from django.conf import settings
from document_processing.schemas.drawing_result import DrawingResult
from document_processing.prompts.drawing_prompt import DRAWING_UNDERSTANDING_PROMPT

logger = logging.getLogger(__name__)

class DrawingUnderstandingService:
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

    def analyze_drawing(self, image_path: str, page_number: int) -> DrawingResult:
        try:
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            response = self.model.generate_content([DRAWING_UNDERSTANDING_PROMPT, img])
            text_response = response.text
            
            # Clean up markdown fences
            if text_response.startswith('```json'):
                text_response = text_response[7:-3].strip()
            elif text_response.startswith('```'):
                text_response = text_response[3:-3].strip()
                
            data = json.loads(text_response)
            data['page_number'] = page_number
            data['confidence'] = 0.95  # Estimate
            
            return DrawingResult(**data)
            
        except Exception as e:
            logger.error(f"Error understanding drawing {image_path}: {str(e)}")
            # Return empty result with nulls
            return DrawingResult(
                page_number=page_number,
                grid_references=[],
                notes=[],
                dimensions=[],
                title_block={},
                revision_history=[],
                description="",
                confidence=0.0
            )
