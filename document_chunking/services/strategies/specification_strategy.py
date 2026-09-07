import re
from uuid import UUID
from langchain_text_splitters import RecursiveCharacterTextSplitter
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class SpecificationChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        section_pattern = re.compile(
            r'^((?:SECTION\s+\d+|\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]*)',
            re.MULTILINE
        )
        
        parts = re.split(r'(?=^(?:SECTION\s+\d+|\d+\.\d+(?:\.\d+)?)\s+[A-Z][^\n]*)', cleaned_text, flags=re.MULTILINE)
        
        chunks = []
        chunk_idx = 0
        current_section = 'Introduction'
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=150,
            separators=['\n\n', '\n', '. ', ' ']
        )
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            match = section_pattern.match(part)
            if match:
                current_section = match.group(1).strip()
                
            if len(part) <= 1500:
                sub_chunks = [part]
            else:
                sub_chunks = splitter.split_text(part)
                
            for part_number, sub_text in enumerate(sub_chunks, 1):
                content = f'Section: {current_section} (part {part_number})\n\n{sub_text}'
                
                metadata = base_meta.copy()
                metadata.update({
                    'chunk_type': 'specification_section',
                    'section_name': current_section,
                    'chunk_part': part_number,
                })
                
                chunks.append(ChunkResult(
                    page_id=UUID(page_id),
                    chunk_index=chunk_idx,
                    chunk_type='specification_section',
                    content=content,
                    metadata=metadata,
                    char_count=len(content),
                    word_count=len(content.split()),
                    strategy_used='SpecificationChunkingStrategy'
                ))
                chunk_idx += 1
                
        return chunks
