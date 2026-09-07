from pydantic import BaseModel, ConfigDict
from .ocr_result import OCRStrategy

class PageAnalysisResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    page_number: int
    contains_tables: bool
    contains_handwriting: bool
    contains_drawing: bool
    contains_stamp: bool
    contains_signature: bool
    contains_revision_block: bool
    contains_title_block: bool
    contains_grid_reference: bool
    recommended_strategy: OCRStrategy
    analysis_confidence: float
