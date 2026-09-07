import logging
from uuid import UUID
from celery import shared_task, chord
from document_refinement.repositories.refinement_repository import RefinementRepository
from document_refinement.tasks.refine_page import refine_page_task

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def refine_document_task(self, document_id: str):
    logger.info(f"Starting refinement for document {document_id}")
    repo = RefinementRepository()
    
    # 1. Load all Pages for this document
    pages_data = repo.get_pages_for_document(UUID(document_id))
    
    if not pages_data:
        logger.warning(f"No pages found needing refinement for document {document_id}")
        return
        
    # 2. Dispatch page tasks using chord
    page_tasks = [refine_page_task.s(str(page['id'])) for page in pages_data]
    
    chord(page_tasks)(refinement_aggregate_task.s(document_id))

@shared_task
def refinement_aggregate_task(results, document_id: str):
    # This is the chord callback
    logger.info(f"Refinement aggregation completed for document {document_id}")
    
    # Avoid circular imports by importing signal here
    from document_refinement.signals import refinement_completed
    
    refinement_completed.send(sender=None, document_id=str(document_id))
    return f"Aggregated {len(results)} pages for document {document_id}"
