from typing import Optional
from pydantic import BaseModel, ConfigDict

class QueryFilters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project_id:     Optional[str] = None
    doc_type:       Optional[str] = None
    trade:          Optional[str] = None
    discipline:     Optional[str] = None
    drawing_number: Optional[str] = None
    revision:       Optional[str] = None
    is_current:     Optional[bool] = None
    floor_level:    Optional[str] = None
    building:       Optional[str] = None
    semantic_query: str
    sub_queries:    list[str]
