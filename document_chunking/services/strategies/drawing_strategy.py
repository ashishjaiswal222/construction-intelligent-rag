from uuid import UUID
from document_chunking.services.strategies.base_strategy import BaseChunkingStrategy
from document_chunking.schemas.chunk_result import ChunkResult

class DrawingChunkingStrategy(BaseChunkingStrategy):

    def chunk(
        self,
        cleaned_text: str,
        page_id: str,
        page_number: int,
        document_metadata: dict,
        extracted_data: dict | None = None,
    ) -> list[ChunkResult]:
        if not extracted_data:
            return []
            
        base_meta = self._base_metadata(document_metadata, page_id, page_number)
        
        drawing_number = extracted_data.get('drawing_number', '')
        title = extracted_data.get('title', '')
        discipline = extracted_data.get('discipline', '')
        revision = extracted_data.get('revision', '')
        status = extracted_data.get('status', '')
        scale = extracted_data.get('scale', '')
        description = extracted_data.get('description', '')
        
        elements = extracted_data.get('elements', [])
        grid_references = extracted_data.get('grid_references', [])
        materials = extracted_data.get('materials', [])
        dimensions = extracted_data.get('dimensions', [])
        floor_levels = extracted_data.get('floor_levels', [])
        cross_references = extracted_data.get('cross_references', [])
        notes = extracted_data.get('notes', [])
        
        content = f"""
DRAWING: {drawing_number} — {title}
TYPE: {discipline.upper() if discipline else ''} | REVISION: {revision}
STATUS: {status} | SCALE: {scale}

DESCRIPTION:
{description}

ELEMENTS: {', '.join(elements)}
GRID REFERENCES: {', '.join(grid_references)}
MATERIALS: {', '.join(materials)}
KEY DIMENSIONS: {', '.join(dimensions)}
FLOOR LEVELS: {', '.join(floor_levels)}
CROSS REFERENCES: {', '.join(cross_references)}
NOTES: {' | '.join(notes[:5])}
        """.strip()
        
        is_current = status in ['IFC', 'As-Built', 'Approved']
        
        metadata = base_meta.copy()
        metadata.update({
            'chunk_type': 'drawing_vision',
            'drawing_number': drawing_number,
            'drawing_discipline': discipline,
            'revision': revision,
            'drawing_status': status,
            'is_current': is_current,
            'grid_refs': '|'.join(grid_references),
            'floor_levels': '|'.join(floor_levels),
            'cross_refs': '|'.join(cross_references),
        })
        
        return [ChunkResult(
            page_id=UUID(page_id),
            chunk_index=0,
            chunk_type='drawing_vision',
            content=content,
            metadata=metadata,
            char_count=len(content),
            word_count=len(content.split()),
            strategy_used='DrawingChunkingStrategy'
        )]
