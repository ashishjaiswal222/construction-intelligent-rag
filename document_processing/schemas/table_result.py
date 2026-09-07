from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any

class TableResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    page_number: int
    table_index: int
    headers: List[str]
    rows: List[List[str]]
    merged_cells: List[Dict[str, Any]]
    confidence: float
    raw_markdown: str
