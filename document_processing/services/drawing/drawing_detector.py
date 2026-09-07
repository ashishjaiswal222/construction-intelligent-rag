class DrawingDetector:
    def detect(self, text: str) -> bool:
        # Simple heuristic, full analysis might use image patterns
        keywords = ['drawing', 'scale', 'revision', 'title block']
        return any(k in text.lower() for k in keywords)
