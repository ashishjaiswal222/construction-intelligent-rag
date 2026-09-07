import logging
from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

logger = logging.getLogger(__name__)

class BOQChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        # extracted_data should contain the tables list for BOQ
        if not extracted_data:
            logger.warning('BOQ page has no extracted table data, falling back')
            return []
            
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        chunks = []
        chunk_idx = 0
        current_section = ''
        current_division = ''
        
        for table in extracted_data:
            rows = table.get('rows', [])
            for row in rows:
                if row.get('is_header'):
                    # Heuristics to update section/division
                    header_text = row.get('text', '')
                    if 'division' in header_text.lower():
                        current_division = header_text
                    else:
                        current_section = header_text
                    continue
                    
                item_number = row.get('item_number', '')
                description = row.get('description', '')
                unit = row.get('unit', '')
                quantity = row.get('quantity', '')
                rate = row.get('rate', '')
                amount = row.get('amount', '')
                
                # Only chunk actual data rows
                if not item_number and not description:
                    continue
                    
                content = (
                    f"BOQ Division: {current_division}\n"
                    f"BOQ Section: {current_section}\n"
                    f"Item Number: {item_number}\n"
                    f"Description: {description}\n"
                    f"Unit: {unit}\n"
                    f"Quantity: {quantity}\n"
                    f"Rate (INR): {rate}\n"
                    f"Amount (INR): {amount}\n"
                    f"Project: {document_metadata.get('project_id', '')}\n"
                    f"BOQ Revision: {document_metadata.get('revision', '')}\n"
                )
                
                metadata = base_meta.copy()
                metadata.update({
                    'chunk_type': 'boq_item',
                    'item_number': item_number,
                    'boq_section': current_section,
                    'boq_division': current_division,
                    'unit': unit,
                    'quantity': str(quantity),
                    'rate': str(rate),
                })
                
                chunks.append(ChunkResult(
                    page_id=UUID(page_id),
                    chunk_index=chunk_idx,
                    chunk_type='boq_item',
                    content=content,
                    metadata=metadata,
                    char_count=len(content),
                    word_count=len(content.split()),
                    strategy_used='BOQChunkingStrategy'
                ))
                chunk_idx += 1
                
        return chunks
