import os
import logging
from PIL import Image, ImageEnhance
from document_processing.services.image.dpi_enhancer import DpiEnhancer

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    def __init__(self):
        self.dpi_enhancer = DpiEnhancer()

    def preprocess(self, image_path: str) -> str:
        """
        1. Call DpiEnhancer
        2. Convert to grayscale ('L' mode)
        3. Apply contrast enhancement (factor = 1.5)
        4. Save as JPEG quality=95 to /tmp/processed_{original_name}
        5. Return new path
        """
        try:
            # 1. Upscale via DpiEnhancer
            enhanced_path = self.dpi_enhancer.enhance(image_path)
            
            with Image.open(enhanced_path) as img:
                # 2. Convert to grayscale
                img = img.convert('L')
                
                # 3. Contrast enhancement
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.5)
                
                # 4. Save
                filename = os.path.basename(image_path)
                os.makedirs('/tmp', exist_ok=True)
                new_path = os.path.join('/tmp', f"processed_{filename}")
                img.save(new_path, "JPEG", quality=95)
                
                return new_path
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {str(e)}")
            return image_path
