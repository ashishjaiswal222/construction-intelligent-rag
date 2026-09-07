import logging

logger = logging.getLogger(__name__)

class OCRQualityService:
    def calculate_quality(self, text: str, confidence: float) -> float:
        """
        Metrics to compute:
          char_count = len(text)
          word_density = len(text.split()) / max(char_count, 1) * 100
          alpha_ratio = sum(c.isalpha() for c in text) / max(char_count, 1)
          symbol_density = sum(not c.isalnum() and not c.isspace() for c in text) / max(char_count, 1)

        Scoring rules:
          base_score = confidence * 0.4
          if char_count > 200: base_score += 0.2
          if 0.4 < alpha_ratio < 0.85: base_score += 0.2
          if symbol_density < 0.15: base_score += 0.1
          if word_density > 10: base_score += 0.1

        overall_quality_score = min(base_score, 1.0)
        """
        if not text:
            return 0.0
            
        char_count = len(text)
        word_density = len(text.split()) / max(char_count, 1) * 100
        alpha_ratio = sum(c.isalpha() for c in text) / max(char_count, 1)
        symbol_density = sum(not c.isalnum() and not c.isspace() for c in text) / max(char_count, 1)

        base_score = confidence * 0.4
        if char_count > 200:
            base_score += 0.2
        if 0.4 < alpha_ratio < 0.85:
            base_score += 0.2
        if symbol_density < 0.15:
            base_score += 0.1
        if word_density > 10:
            base_score += 0.1

        overall_quality_score = min(base_score, 1.0)
        return overall_quality_score
