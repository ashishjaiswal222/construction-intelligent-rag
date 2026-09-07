import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class EngineeringCalcChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        # Split on calculation header patterns
        pattern = re.compile(
            r'^(Calculation:|Check:|Design of:|\d+\.\s+Calculation|\d+\.\s+Design)',
            re.MULTILINE | re.IGNORECASE
        )
        
        parts = re.split(pattern, cleaned_text)
        
        chunks = []
        chunk_idx = 0
        
        if not parts[0].strip():
            parts = parts[1:]
        elif not pattern.match(parts[0]):
            pass # Maybe preamble
            
        def extract(patt, text, default=''):
            m = re.search(patt, text, re.IGNORECASE)
            return m.group(1).strip() if m else default

        for i in range(len(parts)):
            if pattern.match(parts[i]):
                header = parts[i].strip()
                block_text = parts[i+1] if i+1 < len(parts) else ''
                
                title = extract(r'(?:Calculation|Check|Design of):\s*([^\n]+)', header)
                if not title:
                    title = header
                    
                standard = extract(r'(?:Standard|Code):\s*([^\n]+)', block_text)
                
                content = f"{header}\n{block_text}".strip()
                
                metadata = base_meta.copy()
                metadata.update({
                    'chunk_type': 'calc_block',
                    'calc_title': title,
                    'referenced_standard': standard,
                })
                
                chunks.append(ChunkResult(
                    page_id=UUID(page_id),
                    chunk_index=chunk_idx,
                    chunk_type='calc_block',
                    content=content,
                    metadata=metadata,
                    char_count=len(content),
                    word_count=len(content.split()),
                    strategy_used='EngineeringCalcChunkingStrategy'
                ))
                chunk_idx += 1
                
        return chunks
