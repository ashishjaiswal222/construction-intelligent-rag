from typing import Dict, Any, List
from uuid import UUID
from document_processing.models import ExtractedContent

class ContentRepository:
    def save_content(self, page_id: UUID, content_type: str, raw_data: Dict[str, Any], text_preview: str, confidence: float, sequence_order: int) -> ExtractedContent:
        return ExtractedContent.objects.create(
            page_id=page_id,
            content_type=content_type,
            raw_data=raw_data,
            text_preview=text_preview,
            confidence=confidence,
            sequence_order=sequence_order
        )

    def get_content_by_page(self, page_id: UUID) -> List[ExtractedContent]:
        return list(ExtractedContent.objects.filter(page_id=page_id).order_by('sequence_order'))

    def get_content_by_job(self, job_id: UUID, content_types: List[str] = None) -> List[ExtractedContent]:
        qs = ExtractedContent.objects.filter(page__processing_job_id=job_id)
        if content_types:
            qs = qs.filter(content_type__in=content_types)
        return list(qs.order_by('page__page_number', 'sequence_order'))
