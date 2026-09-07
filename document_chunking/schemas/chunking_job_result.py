from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ChunkingJobResult(BaseModel):
    model_config = ConfigDict(extra='forbid')

    document_id: UUID
    job_id: UUID
    total_chunks: int
    chunked_pages: int
    failed_pages: int
    strategy_breakdown: dict[str, int]
    status: str
