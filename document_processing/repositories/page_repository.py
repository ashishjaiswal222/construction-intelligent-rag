from typing import Optional, List
from uuid import UUID
from django.db.models import F
from document_processing.models import Page, OCRResult
from document_processing.schemas.ocr_result import OCRPageResult

class PageRepository:
    def create_page(self, job_id: UUID, document_id: UUID, page_number: int) -> Page:
        return Page.objects.create(
            processing_job_id=job_id,
            document_id=document_id,
            page_number=page_number,
            status=Page.Status.PENDING
        )

    def get_page(self, page_id: UUID) -> Optional[Page]:
        try:
            return Page.objects.get(id=page_id)
        except Page.DoesNotExist:
            return None

    def get_page_by_number(self, job_id: UUID, page_number: int) -> Optional[Page]:
        try:
            return Page.objects.get(processing_job_id=job_id, page_number=page_number)
        except Page.DoesNotExist:
            return None

    def update_status(self, page_id: UUID, status: str, error_message: str = '') -> None:
        Page.objects.filter(id=page_id).update(status=status, error_message=error_message)

    def update_metrics(self, page_id: UUID, strategy_used: str, confidence: float, processing_time_ms: int, char_count: int, quality_score: float) -> None:
        Page.objects.filter(id=page_id).update(
            strategy_used=strategy_used,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            char_count=char_count,
            quality_score=quality_score
        )

    def update_flags(self, page_id: UUID, flags: dict) -> None:
        Page.objects.filter(id=page_id).update(**flags)

    def increment_retry(self, page_id: UUID) -> None:
        Page.objects.filter(id=page_id).update(retry_count=F('retry_count') + 1)

    def save_ocr_result(self, page_id: UUID, result: OCRPageResult, cleaned_text: str) -> OCRResult:
        return OCRResult.objects.create(
            page_id=page_id,
            raw_text=result.text,
            cleaned_text=cleaned_text,
            strategy_used=result.strategy_used,
            confidence=result.confidence,
            char_count=result.char_count,
            word_count=result.word_count,
            processing_ms=result.processing_ms,
            has_handwriting=result.has_handwriting,
            handwriting_segments=result.handwriting_segments
        )

    def get_pages_by_job(self, job_id: UUID) -> List[Page]:
        return list(Page.objects.filter(processing_job_id=job_id).order_by('page_number'))
