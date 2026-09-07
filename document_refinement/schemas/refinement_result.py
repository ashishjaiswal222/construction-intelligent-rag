from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import List

class RefinementResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    page_id: UUID
    raw_text: str
    cleaned_text: str
    refinement_level: str
    layers_applied: List[str]
    quality_before: float
    quality_after: float
    quality_delta: float
    char_count_before: int
    char_count_after: int
    processing_ms: int
    semantic_validation_used: bool
    passed_quality_gate: bool
    needs_human_review: bool
    refinement_flags: List[str]
