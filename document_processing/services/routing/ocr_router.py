from document_processing.schemas.page_analysis import PageAnalysisResult
from document_processing.schemas.ocr_result import OCRStrategy

class OCRRouter:
    def route(self, pdf_path: str, page_num: int, doc_type: str, page_analysis: PageAnalysisResult, text_layer_quality: float = 0.0) -> OCRStrategy:
        """
        Decision tree in strict priority order:
          1. If text layer exists AND quality_score > 0.85 → TEXT_LAYER
          2. Elif page_analysis.contains_handwriting → GEMINI_VISION
          3. Elif page_analysis.contains_drawing → GEMINI_VISION
          4. Elif page_analysis.contains_tables AND doc_type == 'boq' → GEMINI_VISION
          5. Elif doc_type in ['drawing', 'site_log', 'inspection'] → GEMINI_VISION
          6. Else → PADDLE_OCR (with auto-escalation to GEMINI if confidence < 0.78) - Ensemble handles escalation
        """
        if text_layer_quality > 0.85:
            return OCRStrategy.TEXT_LAYER
            
        if page_analysis.contains_handwriting:
            return OCRStrategy.GEMINI_VISION
            
        if page_analysis.contains_drawing:
            return OCRStrategy.GEMINI_VISION
            
        if page_analysis.contains_tables and doc_type == 'boq':
            return OCRStrategy.GEMINI_VISION
            
        if doc_type in ['drawing', 'site_log', 'inspection']:
            return OCRStrategy.GEMINI_VISION
            
        # Returning PADDLE_OCR, but task will use EnsembleService which implements the escalation
        return OCRStrategy.PADDLE_OCR
