from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import List

class OCRStrategy(str, Enum):
    TEXT_LAYER = 'text_layer'
    PADDLE_OCR = 'paddle_ocr'
    GEMINI_VISION = 'gemini_vision'
    ENSEMBLE = 'ensemble'

class OCRPageResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    page_number: int
    text: str
    confidence: float
    strategy_used: OCRStrategy
    has_tables: bool
    has_handwriting: bool
    handwriting_segments: List[str]
    char_count: int
    word_count: int
    processing_ms: int
