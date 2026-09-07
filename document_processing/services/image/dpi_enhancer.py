import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)

class DpiEnhancer:
    def enhance(self, image_path: str) -> str:
        """
        Calculates effective DPI from image dimensions and upscales 
        if below 300 DPI equivalent. Returns processed path.
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                if width < 1200 or height < 1600:
                    scale_factor = max(1200 / width, 1600 / height)
                    new_width = int(width * scale_factor)
                    new_height = int(height * scale_factor)
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    filename = os.path.basename(image_path)
                    os.makedirs('/tmp', exist_ok=True)
                    new_path = os.path.join('/tmp', f"dpi_enhanced_{filename}")
                    
                    if img.mode not in ('L', 'RGB'):
                        img = img.convert('RGB')
                        
                    img.save(new_path, "JPEG", quality=100)
                    return new_path
                return image_path
                
        except Exception as e:
            logger.error(f"Error enhancing DPI for {image_path}: {str(e)}")
            return image_path
