from typing import Optional
from pydantic import BaseModel, ConfigDict

class Citation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    chunk_id:       str
    document_id:    str
    filename:       str
    doc_type:       str
    page_number:    Optional[int] = None
    drawing_number: Optional[str] = None
    clause_number:  Optional[str] = None
    revision:       str
    excerpt:        str
