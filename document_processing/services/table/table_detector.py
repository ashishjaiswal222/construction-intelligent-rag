class TableDetector:
    def detect(self, text: str) -> bool:
        # A simple heuristic based on text content if needed, 
        # but typically PageAnalysis uses layout or simple keywords
        return "table" in text.lower() or "boq" in text.lower()
