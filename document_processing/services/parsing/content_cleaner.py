import re
from typing import Tuple, List, Dict

class ContentCleaner:
    def clean(self, raw_text: str) -> Tuple[str, List[str], List[str]]:
        """
        Cleans OCR text and extracts special segments.
        Returns: (cleaned_text, handwriting_segments, stamp_segments)
        """
        text = raw_text
        
        # 1. OCR Error Corrections
        # "0" before uppercase letter -> "O"
        text = re.sub(r'0([A-Z])', r'O\1', text)
        
        # "l" between digits -> "1"
        text = re.sub(r'(\d)l(\d)', r'\1 1 \2', text) # wait, just '1'
        text = re.sub(r'(\d)l(\d)', r'\g<1>1\g<2>', text) # more robust replacement
        
        # specific word corrections
        replacements = {
            "m3": "m³",
            "m2": "m²",
            "concrele": "concrete",
            "reinforoced": "reinforced",
            "reinforced": "reinforced",
            "specilication": "specification"
        }
        
        for old, new in replacements.items():
            # Use regex for word boundaries if needed, but simple replace might suffice
            # Since some OCR engines might not preserve boundaries, standard replace is safer 
            # but word boundary is better to not replace in middle of valid words
            text = re.sub(rf'\b{old}\b', new, text, flags=re.IGNORECASE)
            
        # 2. Extract markers
        handwriting_segments = []
        stamp_segments = []
        
        # Extract [HW: ...]
        hw_pattern = r'\[HW:\s*(.*?)\]'
        for match in re.finditer(hw_pattern, text):
            handwriting_segments.append(match.group(1).strip())
            
        # Extract [STAMP: ...]
        stamp_pattern = r'\[STAMP:\s*(.*?)\]'
        for match in re.finditer(stamp_pattern, text):
            stamp_segments.append(match.group(1).strip())
            
        # Note: [?unclear] markers are preserved in the text as requested.
        
        # Optionally, remove the markers from the main text if we extracted them
        # text = re.sub(hw_pattern, '', text)
        # text = re.sub(stamp_pattern, '', text)
        # But specification says "[HW: text] markers -> preserve, extract to handwriting_segments list"
        # So we keep them in the text.

        return text, handwriting_segments, stamp_segments
