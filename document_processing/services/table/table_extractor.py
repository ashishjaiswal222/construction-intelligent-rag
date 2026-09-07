import json
import logging
import google.generativeai as genai
from typing import List
from django.conf import settings
from document_processing.schemas.table_result import TableResult
from document_processing.prompts.table_prompt import TABLE_EXTRACTION_PROMPT
from document_processing.exceptions import RateLimitException

logger = logging.getLogger(__name__)

class TableExtractor:
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

    def extract_tables(self, image_path: str, page_number: int) -> List[TableResult]:
        try:
            import PIL.Image
            img = PIL.Image.open(image_path)
            
            response = self.model.generate_content([TABLE_EXTRACTION_PROMPT, img])
            text_response = response.text
            
            # Clean up markdown fences
            if text_response.startswith('```json'):
                text_response = text_response[7:-3].strip()
            elif text_response.startswith('```'):
                text_response = text_response[3:-3].strip()
                
            data = json.loads(text_response)
            
            tables = []
            if 'tables' in data:
                for idx, t_data in enumerate(data['tables']):
                    t_data['page_number'] = page_number
                    t_data['table_index'] = idx
                    
                    try:
                        table = TableResult(**t_data)
                        tables.append(table)
                    except Exception as validation_e:
                        logger.error(f"Validation error for table {idx}: {str(validation_e)}")
            
            return tables
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "quota" in error_str:
                logger.error(f"Rate limit exceeded during table extraction: {str(e)}")
                raise RateLimitException("Gemini API rate limit exceeded") from e
            
            logger.error(f"Error extracting tables from {image_path}: {str(e)}")
            return []
