import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class ContractChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        # Split at clause boundaries using regex
        pattern = re.compile(r'^(\d+\.(?:\d+\.)*\d*)', re.MULTILINE)
        parts = re.split(r'(?=^\d+\.)', cleaned_text, flags=re.MULTILINE)
        
        chunks = []
        current_section = ''
        current_clause = ''
        chunk_idx = 0
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            match = pattern.match(part)
            if not match:
                # Part of the previous text or introduction before any clause
                continue
                
            clause_num = match.group(1)
            clause_text = part[len(clause_num):].strip()
            
            depth = clause_num.count('.')
            
            if depth == 0:
                current_section = clause_num
            if depth == 1:
                current_clause = clause_num
                
            content = f'Clause {clause_num}: {clause_text}'
            if depth >= 2:
                content = f'[Parent: Clause {current_clause}]\n{content}'
                
            metadata = base_meta.copy()
            metadata.update({
                'chunk_type': 'contract_clause',
                'clause_number': clause_num,
                'clause_depth': depth,
                'parent_section': current_section,
                'parent_clause': current_clause,
            })
            
            import logging
            logger = logging.getLogger(__name__)
            if len(content) > 3000:
                logger.warning(f"Contract clause {clause_num} exceeds 3000 characters (len={len(content)}). Not splitting, keeping as one chunk.")

            chunks.append(ChunkResult(
                page_id=UUID(page_id),
                chunk_index=chunk_idx,
                chunk_type='contract_clause',
                content=content,
                metadata=metadata,
                char_count=len(content),
                word_count=len(content.split()),
                strategy_used='ContractChunkingStrategy'
            ))
            chunk_idx += 1
            
        return chunks
