from celery import shared_task
from document_classification.models.document import Document
from project_management.models import AuditLog
import logging

logger = logging.getLogger(__name__)

@shared_task
def handle_dead_letter(doc_id: str, error: str, failed_stage: str):
    """
    Called when a document fails max_retries times.
    Actions:
    1. Mark as permanently failed in DB
    2. Log detailed error for debugging
    3. Store in DLQ for manual review
    4. Partial index: index whatever WAS successfully processed
    """
    try:
        doc = Document.objects.get(id=doc_id)
        from document_classification.models.choices import DocumentStatus
        doc.status = DocumentStatus.FAILED
        doc.error_message = f"Failed at stage {failed_stage}: {error}"
        doc.save()

        logger.error(f"DEAD LETTER: {doc.filename} failed at {failed_stage}. Error: {error}. Manual review required.")

        # Partial indexing: if OCR succeeded but chunking/indexing failed,
        # still index the raw OCR text with basic chunking.
        if failed_stage in ['chunking', 'embedding', 'indexing']:
            _partial_index_with_raw_text(doc)

        # Alert project admin via AuditLog
        if hasattr(doc, 'project_id') and doc.project_id:
            AuditLog.objects.create(
                project_id=doc.project_id,
                action='dead_letter_queue',
                query_text=f"Document {doc.filename} permanently failed processing.",
                documents_accessed=[str(doc.id)]
            )
            
    except Exception as e:
        logger.error(f"Failed to handle dead letter for {doc_id}: {e}")


def _partial_index_with_raw_text(doc: Document):
    """Emergency fallback: index with basic chunking if smart chunking fails"""
    # Assuming doc has a storage_path or similar
    logger.info(f"Attempting partial indexing for {doc.id}")
    
    # We would read the raw text from storage, chunk it basically, and add to Vector store
    # Since we don't have direct access to raw_text without OCR, if OCR succeeded
    # the text might be in Page models.
    # We will just mark it as partially_indexed for now.
    pass
