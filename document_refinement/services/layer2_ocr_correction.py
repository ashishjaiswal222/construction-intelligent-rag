import re
from typing import Tuple, List

class Layer2OCRCorrection:
    def correct(self, text: str) -> Tuple[str, List[str]]:
        """
        Layer 2: OCR Correction
        Runs on: PADDLE_OCR and ENSEMBLE only.
        Fixes character confusion, word fixes, unit fixes, punctuation.
        """
        fixes = []
        corrected = text
        
        # Character confusion
        char_patterns = [
            (r'\b0(?=[A-Z]{2,})', 'O'), # 0 followed by 2+ uppercase
            (r'(\d)l(\d)', r'\g<1>1\g<2>'), # digit l digit -> digit 1 digit
            (r'\bIl\b', 'II'),
            (r'\bI1\b', 'II'),
        ]
        
        for pattern, repl in char_patterns:
            new_text = re.sub(pattern, repl, corrected)
            if new_text != corrected:
                fixes.append(f"fixed_char_confusion_{pattern}")
                corrected = new_text

        # Word fixes (minimum 40 patterns required overall)
        word_fixes = {
            r'\bconcrele\b': 'concrete',
            r'\bspecilication\b': 'specification',
            r'\breinforoced\b': 'reinforced',
            r'\bconstructlon\b': 'construction',
            r'\bmeasuremenl\b': 'measurement',
            r'\bcertilicate\b': 'certificate',
            r'\bquantily\b': 'quantity',
            r'\bdrawlng\b': 'drawing',
            r'\bprojecl\b': 'project',
            r'\bcontracl\b': 'contract',
            r'\bconsultani\b': 'consultant',
            r'\binspeciion\b': 'inspection',
            r'\bprovislons\b': 'provisions',
            r'\barchiteclure\b': 'architecture',
            r'\bstructuraI\b': 'structural',
            r'\bapprovaI\b': 'approval',
            r'\bmalerial\b': 'material',
            r'\bmalerials\b': 'materials',
            r'\bdimenslons\b': 'dimensions',
            r'\belevalion\b': 'elevation',
            r'\bfoundalion\b': 'foundation',
            r'\binstaliation\b': 'installation',
            r'\bagreemenl\b': 'agreement',
            r'\bmainlenance\b': 'maintenance',
            r'\brequiremenls\b': 'requirements',
            r'\bsecilon\b': 'section',
            r'\bsecilons\b': 'sections',
            r'\bequipmenl\b': 'equipment',
            r'\bslandard\b': 'standard',
            r'\btemperature\b': 'temperature', # just in case
            r'\bwalter\b': 'water', # common
            r'\btesilng\b': 'testing',
            r'\bwealher\b': 'weather',
            r'\bthicknass\b': 'thickness'
        }
        
        for pattern, repl in word_fixes.items():
            new_text = re.sub(pattern, repl, corrected, flags=re.IGNORECASE)
            if new_text != corrected:
                fixes.append(f"fixed_word_{repl}")
                corrected = new_text
                
        # Unit fixes
        unit_patterns = [
            (r'\bm3\b', 'm³'),
            (r'\bm2\b', 'm²'),
            (r'\bcbm\b|\bCUM\b', 'm³'),
            (r'\bsqm\b|\bSQM\b', 'm²'),
        ]
        
        for pattern, repl in unit_patterns:
            new_text = re.sub(pattern, repl, corrected)
            if new_text != corrected:
                fixes.append(f"fixed_unit_{repl}")
                corrected = new_text
                
        # Punctuation
        punc_patterns = [
            (r'\s+,', ','),
            (r',(?=[^\s\d])', ', ')
        ]
        
        for pattern, repl in punc_patterns:
            new_text = re.sub(pattern, repl, corrected)
            if new_text != corrected:
                fixes.append("fixed_punctuation")
                corrected = new_text

        return corrected, list(set(fixes))
