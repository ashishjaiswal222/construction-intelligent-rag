import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class EmailChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        # Split on email headers: From:
        pattern = re.compile(r'^(?=From:)', re.MULTILINE)
        parts = re.split(pattern, cleaned_text)
        
        chunks = []
        chunk_idx = 0
        
        def extract(patt, text, default=''):
            m = re.search(patt, text, re.IGNORECASE)
            return m.group(1).strip() if m else default

        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            sender = extract(r'From:\s*([^\n]+)', part)
            date = extract(r'Date:\s*([^\n]+)', part)
            subject = extract(r'Subject:\s*([^\n]+)', part)
            
            subject_normalized = re.sub(r'^(?:Re|Fwd|FW|RE):\s*', '', subject, flags=re.IGNORECASE).strip()
            
            content = part
            
            metadata = base_meta.copy()
            metadata.update({
                'chunk_type': 'email_thread',
                'from': sender,
                'subject': subject,
                'email_date': date,
                'thread_id': subject_normalized,
            })
            
            chunks.append(ChunkResult(
                page_id=UUID(page_id),
                chunk_index=chunk_idx,
                chunk_type='email_thread',
                content=content,
                metadata=metadata,
                char_count=len(content),
                word_count=len(content.split()),
                strategy_used='EmailChunkingStrategy'
            ))
            chunk_idx += 1
            
        return chunks
