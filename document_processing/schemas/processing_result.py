from pydantic import BaseModel, ConfigDict
from typing import Dict
from uuid import UUID

class ProcessingResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    document_id: UUID
    processing_job_id: UUID
    total_pages: int
    completed_pages: int
    failed_pages: int
    strategy_breakdown: Dict[str, int]
    overall_quality_score: float
    processing_time_seconds: float
    status: str
