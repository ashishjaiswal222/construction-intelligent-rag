from pydantic import BaseModel, Field
from typing import Optional, List

class FileAnalysisResult(BaseModel):
    mime_type: str
    file_hash: str
    file_size: int
    page_count: Optional[int] = None
    preview_text: str = ""
    has_images: bool = False

class DocumentClassification(BaseModel):
    doc_type: str = Field(description="One of the DOC_TYPE_CHOICES")
    doc_sub_type: str = Field(default="", description="e.g. 'FIDIC Red Book' for contract")
    confidence: float = Field(description="Overall Confidence score between 0.0 and 1.0")
    layout_confidence: float = Field(default=0.0, description="Confidence in layout structure")
    ocr_confidence: float = Field(default=0.0, description="Confidence in text extraction readability")
    
    has_tables: bool = Field(default=False)
    has_images: bool = Field(default=False)
    has_drawings: bool = Field(default=False)
    has_handwriting: bool = Field(default=False)
    
    contains_stamp: bool = Field(default=False)
    contains_signature: bool = Field(default=False)
    contains_revision_block: bool = Field(default=False)
    contains_title_block: bool = Field(default=False)
    contains_grid_reference: bool = Field(default=False)
    
    language: str = Field(default="en", description="'en', 'hi', or 'mixed'")
    ocr_required: bool = Field(default=False, description="Is text layer sufficient?")
    ocr_strategy: str = Field(default="none_needed", description="'paddle', 'gemini', 'ensemble'")
    chunking_strategy: str = Field(default="section_preserving")
    priority_metadata: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="", description="Why this classification was chosen")
