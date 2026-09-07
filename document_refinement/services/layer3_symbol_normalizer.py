import re
from typing import Tuple, List

class Layer3SymbolNormalizer:
    def normalize(self, text: str) -> Tuple[str, List[str]]:
        """
        Layer 3: Symbol Normalizer
        Runs on: all strategies.
        Normalizes engineering symbols and expands grades.
        """
        fixes = []
        normalized = text
        
        # Engineering symbols
        symbol_patterns = [
            (r'[Φφ⌀∅]', 'Ø'),
            (r'(?<=\d)\s*(?:deg\.|degrees|deg)\b', '°'),
            (r'\+/-', '±'),
            (r'>=', '≥'),
            (r'<=', '≤'),
            (r'\bN/mm2\b', 'N/mm²'),
            (r'\bkN/m2\b', 'kN/m²'),
        ]
        
        for pattern, repl in symbol_patterns:
            new_text = re.sub(pattern, repl, normalized)
            if new_text != normalized:
                fixes.append(f"normalized_symbol_{repl}")
                normalized = new_text
                
        # Grade expansion
        grade_patterns = {
            r'\bC20\b': 'Grade C20 (20 N/mm² concrete)',
            r'\bC25\b': 'Grade C25 (25 N/mm² concrete)',
            r'\bC30\b': 'Grade C30 (30 N/mm² concrete)',
            r'\bC35\b': 'Grade C35 (35 N/mm² concrete)',
            r'\bC40\b': 'Grade C40 (40 N/mm² concrete)',
            r'\bFe500\b': 'Grade Fe500 rebar (500 N/mm²)',
            r'\bFe415\b': 'Grade Fe415 rebar (415 N/mm²)',
            r'\bTMT\b': 'TMT (Thermo-Mechanically Treated) rebar',
            r'\bHYSD\b': 'HYSD (High Yield Strength Deformed) rebar',
        }
        
        for pattern, repl in grade_patterns.items():
            new_text = re.sub(pattern, repl, normalized)
            if new_text != normalized:
                fixes.append(f"expanded_grade_{repl.split(' ')[0]}")
                normalized = new_text
                
        return normalized, list(set(fixes))
