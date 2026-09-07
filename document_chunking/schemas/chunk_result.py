from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ChunkResult(BaseModel):
    model_config = ConfigDict(extra='forbid')

    page_id: UUID
    chunk_index: int
    chunk_type: str
    content: str
    metadata: dict
    char_count: int
    word_count: int
    strategy_used: str
