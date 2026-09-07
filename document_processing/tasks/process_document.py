import logging
from celery import shared_task, chain, chord
from document_processing.repositories.processing_repository import ProcessingRepository
from document_processing.models import ProcessingJob
from document_processing.utils.pdf_utils import get_page_count
from document_classification.models import Document
# To avoid circular import at load time, import specific tasks inside or use string refs
# We will use string references for dispatch

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_document_task(self, document_id: str):
    """
    Orchestrator task. Called by signal receiver.
    Steps:
    1. Create ProcessingJob record (status=SPLITTING)
    2. Open PDF with PyMuPDF -> get page_count
    3. Update ProcessingJob.total_pages
    4. For each page: dispatch process_page_task.delay(job_id, page_num)
    5. Dispatch aggregate_results_task (use Celery chord or chain)
    6. Update ProcessingJob status=PROCESSING
    On failure: exponential backoff 60s -> 120s -> 240s
    """
    repo = ProcessingRepository()
    try:
        try:
            doc = Document.objects.get(id=document_id)
        except Document.DoesNotExist:
            logger.info(f"Document {document_id} not found (likely deleted). Aborting orchestrator task.")
            return
            
        from document_classification.models.choices import DocumentStatus
        Document.objects.filter(id=document_id).update(status=DocumentStatus.OCR_PROCESSING)
        
        # 1. Create ProcessingJob record (status=SPLITTING)
        job = repo.create_job(document_id)
        repo.update_status(job.id, ProcessingJob.Status.SPLITTING)
        
        # 2. Open PDF with PyMuPDF -> get page_count
        # Assuming Document model has a storage_path field
        pdf_path = getattr(doc, 'storage_path', None) or (doc.file.path if hasattr(doc, 'file') and doc.file else getattr(doc, 'file_path', None))
        
        if not pdf_path:
            raise ValueError(f"Document {document_id} has no valid file path.")
            
        page_count = get_page_count(pdf_path)
        
        if page_count == 0:
            repo.update_status(job.id, ProcessingJob.Status.FAILED, "Page count is 0 or PDF is invalid")
            return
            
        # 3. Update ProcessingJob.total_pages
        repo.set_total_pages(job.id, page_count)
        
        # 4. For each page: dispatch process_page_task
        from .process_page import process_page_task
        
        # Using Celery chord: header is a list of page tasks, callback is an aggregation task (optional but requested)
        page_tasks = [process_page_task.s(str(job.id), page_num) for page_num in range(1, page_count + 1)]
        
        # We can implement a dummy aggregate_results_task if required, or simply use group
        # But specification says: "5. Dispatch aggregate_results_task (use Celery chord or chain)"
        from .aggregate_results import aggregate_results_task
        
        chord_flow = chord(page_tasks)(aggregate_results_task.s(str(job.id)))
        
        # 6. Update ProcessingJob status=PROCESSING
        repo.update_status(job.id, ProcessingJob.Status.PROCESSING)
        
    except Exception as exc:
        logger.error(f"Error in process_document_task for doc {document_id}: {str(exc)}")
        # Exponential backoff
        retry_delay = self.default_retry_delay * (2 ** self.request.retries)
        # Attempt to mark failed if it's the last retry
        if self.request.retries >= self.max_retries:
             # We might not have a job variable if creation failed
             pass
        raise self.retry(exc=exc, countdown=retry_delay)

