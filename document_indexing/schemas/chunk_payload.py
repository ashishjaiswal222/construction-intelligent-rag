from typing import Optional
from pydantic import BaseModel, ConfigDict

class ChunkPayload(BaseModel):
    model_config = ConfigDict(extra='forbid')

    # Identity
    chunk_id: str           # Phase 4 chunk UUID as string
    document_id: str        # parent document UUID
    collection_name: str    # Chroma collection

    # Content
    raw_text: str           # original chunk text from Phase 4
    preprocessed_text: str = '' # after abbreviation expansion
    content_hash: str = ''  # MD5 of preprocessed_text for token caching

    # Phase 5 Metadata (all pass-through as Chroma filter fields)
    # Identity group
    title: Optional[str] = None
    doc_number: Optional[str] = None
    doc_type: Optional[str] = None

    # Version group
    revision: Optional[str] = None
    is_current: bool = True
    approval_status: Optional[str] = None

    # Project group
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    project_phase: Optional[str] = None

    # Location group
    building: Optional[str] = None
    floor_level: Optional[str] = None
    zone: Optional[str] = None

    # Discipline group
    discipline: Optional[str] = None
    trade: Optional[str] = None
    drawing_number: Optional[str] = None

    # Parties group
    main_contractor: Optional[str] = None
    author: Optional[str] = None

    # Quality
    metadata_confidence: float = 0.0
    chunk_sequence: int = 0       # position of chunk within document
    total_chunks: int = 0         # total chunks in this document
