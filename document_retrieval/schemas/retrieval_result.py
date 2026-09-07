from typing import Optional
from pydantic import BaseModel, ConfigDict

class RetrievedChunk(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chunk_id:       str
    content:        str
    doc_type:       str
    document_id:    str
    project_id:     str
    filename:       str
    revision:       str
    is_current:     bool
    drawing_number: Optional[str] = None
    clause_number:  Optional[str] = None
    page_number:    Optional[int] = None
    chunk_type:     str
    score:          float

class RetrievalResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chunks:             list[RetrievedChunk]
    needs_fallback:     bool
    filter_used:        dict
    candidates_found:   int
    final_count:        int
    stages_completed:   list[str]
    processing_ms:      int
