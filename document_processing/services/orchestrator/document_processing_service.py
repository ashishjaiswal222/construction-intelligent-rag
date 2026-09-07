import logging
from uuid import UUID
from document_processing.repositories.processing_repository import ProcessingRepository
from document_processing.repositories.page_repository import PageRepository
from document_processing.models import ProcessingJob

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    def __init__(self, processing_repo: ProcessingRepository, page_repo: PageRepository):
        self.processing_repo = processing_repo
        self.page_repo = page_repo

    def create_job(self, document_id: UUID) -> ProcessingJob:
        return self.processing_repo.create_job(document_id)

    def update_job_status(self, job_id: UUID, status: str, error_message: str = ""):
        self.processing_repo.update_status(job_id, status, error_message)

    def set_total_pages(self, job_id: UUID, total_pages: int):
        self.processing_repo.set_total_pages(job_id, total_pages)
