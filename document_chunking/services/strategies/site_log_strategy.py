import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class SiteLogChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        pattern = re.compile(
            r'^(Date:\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+\w+\s+\d{4})',
            re.MULTILINE | re.IGNORECASE
        )
        
        parts = re.split(pattern, cleaned_text)
        
        chunks = []
        chunk_idx = 0
        
        # parts will be: [text_before_first_match, match1, text1, match2, text2, ...]
        if not parts[0].strip():
            parts = parts[1:]
        elif not pattern.match(parts[0]):
            # If the first part is text before a date, it might be preamble, we can attach it to the first log or skip
            # We'll just look for date headers
            pass
            
        def extract(patt, text, default=''):
            m = re.search(patt, text, re.IGNORECASE)
            return m.group(1).strip() if m else default

        for i in range(len(parts)):
            if pattern.match(parts[i]):
                date_str = parts[i].strip()
                if date_str.lower().startswith('date:'):
                    date_str = date_str[5:].strip()
                    
                entry_text = parts[i+1] if i+1 < len(parts) else ''
                
                weather = extract(r'Weather:\s*([^\n]+)', entry_text)
                temperature = extract(r'Temperature:\s*([^\n]+)', entry_text)
                manpower = extract(r'Manpower:\s*([^\n]+)', entry_text)
                location = extract(r'Location:\s*([^\n]+)', entry_text)
                signed_by = extract(r'(?:Engineer Signature|Signed By):\s*([^\n]+)', entry_text)
                
                activities = extract(r'ACTIVITIES:\s*(.*?)(?=MATERIALS DELIVERED:|ISSUES/OBSERVATIONS:|Engineer Signature|$)', entry_text, '').strip()
                materials = extract(r'MATERIALS DELIVERED:\s*(.*?)(?=ISSUES/OBSERVATIONS:|Engineer Signature|$)', entry_text, '').strip()
                issues = extract(r'ISSUES/OBSERVATIONS:\s*(.*?)(?=Engineer Signature|$)', entry_text, '').strip()
                
                content = (
                    f"Date: {date_str}\n"
                    f"Weather: {weather}\n"
                    f"Temperature: {temperature}\n"
                    f"Manpower: {manpower}\n"
                    f"\nACTIVITIES:\n{activities}\n"
                    f"\nMATERIALS DELIVERED:\n{materials}\n"
                    f"\nISSUES/OBSERVATIONS:\n{issues}\n"
                    f"Engineer Signature: {signed_by}\n"
                )
                
                metadata = base_meta.copy()
                metadata.update({
                    'chunk_type': 'site_log_daily',
                    'log_date': date_str,
                    'location': location,
                })
                
                chunks.append(ChunkResult(
                    page_id=UUID(page_id),
                    chunk_index=chunk_idx,
                    chunk_type='site_log_daily',
                    content=content,
                    metadata=metadata,
                    char_count=len(content),
                    word_count=len(content.split()),
                    strategy_used='SiteLogChunkingStrategy'
                ))
                chunk_idx += 1
                
        return chunks
