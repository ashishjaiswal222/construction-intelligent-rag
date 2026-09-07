import cv2
import numpy as np
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class StampDetector:
    def detect(self, image_path: str) -> dict:
        """
        - Convert to grayscale
        - Apply Otsu threshold
        - Find contours with aspect ratio near 1.0 (circular stamps) or rectangular
        - Return StampDetectionResult(found: bool, regions: list[dict])
        """
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {"found": False, "regions": []}
                
            # Otsu threshold
            _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            regions = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = cv2.contourArea(cnt)
                
                # Filter small noise
                if area < 1000:
                    continue
                    
                aspect_ratio = float(w) / h
                # Circular or rectangular stamp approximations
                if 0.8 <= aspect_ratio <= 1.2 or 1.5 <= aspect_ratio <= 3.0:
                    regions.append({
                        "x": x, "y": y, "w": w, "h": h, "aspect_ratio": aspect_ratio
                    })
            
            return {
                "found": len(regions) > 0,
                "regions": regions
            }
        except Exception as e:
            logger.error(f"Error detecting stamps in {image_path}: {str(e)}")
            return {"found": False, "regions": []}
