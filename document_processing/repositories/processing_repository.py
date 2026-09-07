from typing import Optional, Dict
from uuid import UUID
from django.db.models import F
from document_processing.models import ProcessingJob

class ProcessingRepository:
    def create_job(self, document_id: UUID) -> ProcessingJob:
        return ProcessingJob.objects.create(
            document_id=document_id,
            status=ProcessingJob.Status.PENDING
        )

    def get_job(self, job_id: UUID) -> Optional[ProcessingJob]:
        try:
            return ProcessingJob.objects.get(id=job_id)
        except ProcessingJob.DoesNotExist:
            return None

    def get_job_by_document(self, document_id: UUID) -> Optional[ProcessingJob]:
        return ProcessingJob.objects.filter(document_id=document_id).order_by('-created_at').first()

    def update_status(self, job_id: UUID, status: str, error_message: str = '') -> None:
        ProcessingJob.objects.filter(id=job_id).update(
            status=status,
            error_message=error_message
        )

    def set_total_pages(self, job_id: UUID, total_pages: int) -> None:
        ProcessingJob.objects.filter(id=job_id).update(total_pages=total_pages)

    def increment_processed_pages(self, job_id: UUID) -> None:
        ProcessingJob.objects.filter(id=job_id).update(
            processed_pages=F('processed_pages') + 1
        )

    def increment_failed_pages(self, job_id: UUID) -> None:
        ProcessingJob.objects.filter(id=job_id).update(
            failed_pages=F('failed_pages') + 1
        )

    def update_meta(self, job_id: UUID, meta: Dict) -> None:
        ProcessingJob.objects.filter(id=job_id).update(processing_meta=meta)
