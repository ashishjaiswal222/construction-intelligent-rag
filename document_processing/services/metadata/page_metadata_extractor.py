from document_processing.schemas.page_analysis import PageAnalysisResult
from document_processing.schemas.ocr_result import OCRStrategy

class PageMetadataExtractor:
    def extract(self, page_number: int, text: str = "", doc_type: str = "") -> PageAnalysisResult:
        # Improved heuristic logic to save Gemini Vision tokens
        text_lower = text.lower()
        
        import re
        
        # Look for table structures or keywords rather than blindly flagging whole documents
        has_table_keyword = "table" in text_lower
        
        # If it's a BOQ, don't flag every page. Only flag if BOQ tabular data is likely present.
        boq_keywords = ["qty", "quantity", "rate", "amount", "unit", "item", "description"]
        has_boq_table = doc_type == 'boq' and sum(1 for kw in boq_keywords if kw in text_lower) >= 2
        
        # Check for grid-like ascii characters common in raw PDF text extraction of tables
        grid_pattern = re.compile(r'(\|.*?\||[\-\+]{5,})')
        has_grid = bool(grid_pattern.search(text))
        
        contains_tables = has_table_keyword or has_boq_table or has_grid
        
        contains_drawing = doc_type == 'drawing' or "drawing" in text_lower or "scale" in text_lower
        contains_handwriting = "[HW:" in text
        
        return PageAnalysisResult(
            page_number=page_number,
            contains_tables=contains_tables,
            contains_handwriting=contains_handwriting,
            contains_drawing=contains_drawing,
            contains_stamp=False,
            contains_signature=False,
            contains_revision_block=False,
            contains_title_block=False,
            contains_grid_reference=False,
            recommended_strategy=OCRStrategy.PADDLE_OCR,
            analysis_confidence=0.5
        )
