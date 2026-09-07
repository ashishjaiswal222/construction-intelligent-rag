from uuid import UUID
from langchain_text_splitters import RecursiveCharacterTextSplitter
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class GenericChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=['\n\n', '\n', '. ', ' ']
        )
        
        text_chunks = splitter.split_text(cleaned_text)
        
        chunks = []
        for idx, text_chunk in enumerate(text_chunks):
            metadata = base_meta.copy()
            metadata.update({
                'chunk_type': 'generic',
                'fallback_reason': 'unknown doc type or fallback',
            })
            
            chunks.append(ChunkResult(
                page_id=UUID(page_id),
                chunk_index=idx,
                chunk_type='generic',
                content=text_chunk,
                metadata=metadata,
                char_count=len(text_chunk),
                word_count=len(text_chunk.split()),
                strategy_used='GenericChunkingStrategy'
            ))
            
        return chunks
