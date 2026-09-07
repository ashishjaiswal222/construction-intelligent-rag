from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from .citation import Citation

class GenerationResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    log_id:             Optional[str] = None
    answer:             str
    citations:          List[Citation]
    confidence:         float
    needs_fallback:     bool
    answer_grounded:    bool
    warning_message:    Optional[str] = None
    retrieval_stages:   List[str]
    processing_ms:      int
