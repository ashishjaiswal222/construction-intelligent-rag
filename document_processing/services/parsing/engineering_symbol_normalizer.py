class EngineeringSymbolNormalizer:
    def normalize(self, text: str) -> str:
        """
        Normalize engineering symbols:
          Φ, φ, ⌀ variants → standard phi character
          ° variants → degree symbol
          Δ → Delta
          ω → omega
          ± → plus-minus
          ≥, ≤ → comparison operators
        """
        replacements = {
            'Φ': 'Φ',
            'φ': 'Φ',
            '⌀': 'Φ', # Standardize to capital Phi
            'degree': '°',
            'degrees': '°',
            'deg.': '°',
            'Δ': 'Δ',
            'omega': 'ω',
            '+/-': '±',
            '>=': '≥',
            '<=': '≤'
        }
        
        normalized = text
        for old, new in replacements.items():
            # Only apply for non-single-char keys if using simple replace to avoid breaking words
            if len(old) > 1:
                normalized = normalized.replace(old, new)
            else:
                normalized = normalized.replace(old, new)
                
        return normalized
