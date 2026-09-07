import re
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class RFIChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        # Look for RFI pattern: 'RFI Number:', 'QUESTION:', 'RESPONSE:', 'Drawing References:'
        if 'QUESTION:' not in cleaned_text or 'RESPONSE:' not in cleaned_text:
            return []
            
        def extract(pattern, text, default=''):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else default
            
        rfi_number = extract(r'RFI Number:\s*([^\n]+)', cleaned_text)
        date = extract(r'Date Submitted:\s*([^\n]+)', cleaned_text)
        submitted_by = extract(r'Submitted By:\s*([^\n]+)', cleaned_text)
        drawing_refs = extract(r'Drawing References?:\s*([^\n]+)', cleaned_text)
        spec_refs = extract(r'Specification References?:\s*([^\n]+)', cleaned_text)
        
        question = extract(r'(?s)QUESTION:\s*(.*?)(?=RESPONSE:|$)', cleaned_text, '').strip()
        response = extract(r'(?s)RESPONSE:\s*(.*?)(?=Response Date:|Responded By:|$)', cleaned_text, '').strip()
        
        response_date = extract(r'Response Date:\s*([^\n]+)', cleaned_text)
        responded_by = extract(r'Responded By:\s*([^\n]+)', cleaned_text)
        
        content = (
            f"RFI Number: {rfi_number}\n"
            f"Date Submitted: {date}\n"
            f"Submitted By: {submitted_by}\n"
            f"Drawing References: {drawing_refs}\n"
            f"Specification References: {spec_refs}\n"
            f"\nQUESTION:\n{question}\n"
            f"\nRESPONSE:\n{response}\n"
            f"Response Date: {response_date}\n"
            f"Responded By: {responded_by}\n"
        )
        
        metadata = base_meta.copy()
        metadata.update({
            'chunk_type': 'rfi_qa_pair',
            'rfi_number': rfi_number,
            'drawing_refs': drawing_refs,
            'is_answered': bool(response and response != 'Not yet responded'),
        })
        
        return [ChunkResult(
            page_id=UUID(page_id),
            chunk_index=0,
            chunk_type='rfi_qa_pair',
            content=content,
            metadata=metadata,
            char_count=len(content),
            word_count=len(content.split()),
            strategy_used='RFIChunkingStrategy'
        )]
