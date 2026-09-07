# Phase 4: Data Models & Storage

Phase 4 utilizes a robust storage architecture to track the chunking process and store the final semantic data before it is embedded into the Vector Database.

## 1. Django Models (`models/`)

### `ChunkingJob`
Tracks the progress of a document through the Phase 4 pipeline.
- `id`: UUID primary key.
- `document_id`: UUID reference to the Phase 1 `Document`. (Note: We use UUIDs rather than direct ForeignKeys to avoid cross-app ORM coupling).
- `status`: Enum (`PENDING`, `PROCESSING`, `COMPLETED`, `FAILED`, `PARTIAL`, `AGGREGATING`).
- `total_pages`, `chunked_pages`, `failed_pages`: Counters for progress and error tracking.
- `total_chunks`: The final count of all chunks produced for this document.
- `strategy_breakdown`: JSON field recording which strategies were used (e.g., `{'generic': 10, 'contract_clause': 5}`).
- `started_at`, `completed_at`: Timestamps for pipeline timing and performance monitoring.
- `error_message`: Text field for debugging.

### `DocumentChunk`
The final resting place for the refined, chunked text.
- `chunk_index`: The sequential order of the chunk in the document.
- `chunk_type`: The semantic type of the chunk (e.g., `contract_clause`, `rfi_qa_pair`).
- `content`: The actual text payload.
- `is_current`, `doc_type`, `revision`: Explicit database columns indexed for high-performance vector-filtering. `is_current` is essential for massive hallucination reduction.
- `metadata`: JSON field containing additional metadata (`page_number`, `project_id`, `language`, etc.).
- `strategy_used`: The name of the Python class that generated the chunk.

## 2. Pydantic Schemas (`schemas/`)

To prevent dirty data from entering the database or vector store, Phase 4 enforces strict validation using Pydantic v2.

### `ChunkResult`
```python
from pydantic import BaseModel, ConfigDict, Field

class ChunkResult(BaseModel):
    model_config = ConfigDict(extra='forbid')

    document_id: str
    page_id: str
    chunk_index: int
    chunk_type: str
    content: str
    metadata: dict = Field(default_factory=dict)
    char_count: int
    word_count: int
    strategy_used: str
```
By enforcing `extra='forbid'`, we ensure that no rogue scripts or strategies can inject arbitrary undocumented fields into our chunk metadata, maintaining strict compliance with the Phase 5 Vector Indexing requirements.
