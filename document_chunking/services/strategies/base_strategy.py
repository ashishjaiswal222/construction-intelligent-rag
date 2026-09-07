from abc import ABC, abstractmethod
from document_chunking.schemas.chunk_result import ChunkResult

class BaseChunkingStrategy(ABC):

    @abstractmethod
    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        """
        All strategies implement this interface.
        cleaned_text: the Phase 3 refined text for this page
        page_id: UUID string of the Phase 2 page
        page_number: int
        document_metadata: dict from chunking_repository.get_document_context()
        extracted_data: tables or drawing JSON from Phase 2 (if any)
        Returns: list of ChunkResult objects
        """

    def _base_metadata(self, document_metadata: dict, page_id: str,
                       page_number: int) -> dict:
        """
        Every chunk gets these fields in metadata regardless of type.
        This ensures all filters work at retrieval time.
        """
        return {
            'document_id': str(document_metadata.get('document_id', '')),
            'doc_type': document_metadata.get('doc_type', ''),
            'project_id': str(document_metadata.get('project_id', '')),
            'filename': document_metadata.get('filename', ''),
            'revision': document_metadata.get('revision', ''),
            'is_current': document_metadata.get('is_current', True),
            'language': document_metadata.get('language', 'en'),
            'page_id': str(page_id),
            'page_number': page_number,
        }
