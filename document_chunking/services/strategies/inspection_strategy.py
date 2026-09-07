import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class InspectionChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        # Split by sections if they exist, or just find items
        section_pattern = re.compile(r'^Section:\s*([^\n]+)', re.MULTILINE | re.IGNORECASE)
        sections = re.split(r'(?=^Section:\s*[^\n]+)', cleaned_text, flags=re.MULTILINE | re.IGNORECASE)
        
        chunks = []
        chunk_idx = 0
        
        inspection_date = ''
        inspector_name = ''
        
        # Global header extraction
        match_date = re.search(r'Date:\s*([^\n]+)', cleaned_text, re.IGNORECASE)
        if match_date:
            inspection_date = match_date.group(1).strip()
            
        match_inspector = re.search(r'Inspector:\s*([^\n]+)', cleaned_text, re.IGNORECASE)
        if match_inspector:
            inspector_name = match_inspector.group(1).strip()
            
        # Item pattern: 1. Item description [YES|NO|PASS|FAIL] Remarks: ...
        item_pattern = re.compile(
            r'^(\d+)\.\s+(.*?)(?:\[|)(YES|NO|PASS|FAIL)(?:\]|)\s*(?:Remarks:\s*(.*))?$',
            re.MULTILINE | re.IGNORECASE
        )

        for part in sections:
            part = part.strip()
            if not part:
                continue
                
            section_name = 'General'
            sec_match = section_pattern.match(part)
            if sec_match:
                section_name = sec_match.group(1).strip()
                
            for match in item_pattern.finditer(part):
                item_number = match.group(1).strip()
                item_description = match.group(2).strip()
                result = match.group(3).strip().upper()
                remarks = match.group(4).strip() if match.group(4) else ''
                
                content = (
                    f"Inspection Section: {section_name}\n"
                    f"Item {item_number}: {item_description}\n"
                    f"Result: {result}\n"
                    f"Remarks: {remarks}\n"
                    f"Date: {inspection_date}\n"
                    f"Inspector: {inspector_name}\n"
                )
                
                metadata = base_meta.copy()
                metadata.update({
                    'chunk_type': 'inspection_item',
                    'inspection_section': section_name,
                    'item_number': item_number,
                    'result': result,
                    'inspection_date': inspection_date,
                })
                
                chunks.append(ChunkResult(
                    page_id=UUID(page_id),
                    chunk_index=chunk_idx,
                    chunk_type='inspection_item',
                    content=content,
                    metadata=metadata,
                    char_count=len(content),
                    word_count=len(content.split()),
                    strategy_used='InspectionChunkingStrategy'
                ))
                chunk_idx += 1
                
        return chunks
