from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class DrawingResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    page_number: int
    drawing_number: Optional[str] = None
    sheet_number: Optional[str] = None
    revision: Optional[str] = None
    discipline: Optional[str] = None
    title: Optional[str] = None
    scale: Optional[str] = None
    grid_references: List[str]
    notes: List[str]
    dimensions: List[str]
    title_block: Dict[str, Any]
    revision_history: List[Dict[str, Any]]
    description: str
    confidence: float
