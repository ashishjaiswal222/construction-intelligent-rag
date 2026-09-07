import logging
from celery import shared_task
from django.utils import timezone
from ..models.document import Document
from ..models.choices import DocumentStatus
from ..models.audit import DocumentClassificationHistory
from ..services.classifier_service import ClassifierService
from shared.events import classification_completed, classification_failed

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def classify_document_task(self, doc_id: str):
    """
    Async document classification task.
    Retries up to 3 times on failure with exponential backoff.
    """
    try:
        doc = Document.objects.get(id=doc_id)
    except Document.DoesNotExist:
        logger.error(f'Document not found: {doc_id}')
        return

    doc.status = DocumentStatus.CLASSIFYING
    doc.save(update_fields=['status', 'updated_at'])

    try:
        service = ClassifierService()
        result = service.process_document(doc)

        doc.doc_type = result.doc_type
        doc.doc_subtype = result.doc_sub_type
        doc.classification_confidence = result.confidence
        doc.layout_confidence = result.layout_confidence
        doc.ocr_confidence = result.ocr_confidence
        
        doc.has_tables = result.has_tables
        doc.has_drawings = result.has_drawings
        doc.has_handwriting = result.has_handwriting
        
        doc.contains_stamp = result.contains_stamp
        doc.contains_signature = result.contains_signature
        doc.contains_revision_block = result.contains_revision_block
        doc.contains_title_block = result.contains_title_block
        doc.contains_grid_reference = result.contains_grid_reference
        
        doc.language = result.language
        
        if result.doc_type != 'unknown' and result.confidence >= 0.75:
            doc.status = DocumentStatus.CLASSIFIED
        else:
            doc.status = DocumentStatus.NEEDS_REVIEW
            
        doc.classifier_used = 'llm_factory'
        doc.save()

        # Create Audit Log
        DocumentClassificationHistory.objects.create(
            document=doc,
            classifier_name=doc.classifier_used,
            doc_type_predicted=doc.doc_type,
            confidence=doc.classification_confidence,
            raw_response=result.model_dump_json()
        )

        logger.info(f'Classified {doc.filename}: {result.doc_type} ({result.confidence:.2f})')
        
        # Fire Event for Orchestrator
        classification_completed.send(sender=self.__class__, document_id=doc.id, doc_type=doc.doc_type)
        
        return {'status': 'success', 'doc_type': result.doc_type}

    except Exception as exc:
        logger.error(f'Classification failed for {doc_id}: {exc}')
        
        # Check if document was deleted by the user while the task was running
        if not Document.objects.filter(id=doc_id).exists():
            logger.warning(f"Document {doc_id} was deleted. Aborting task gracefully.")
            return

        doc.error_message = str(exc)
        doc.retry_count += 1
        
        if self.request.retries >= self.max_retries:
            doc.status = DocumentStatus.FAILED
            doc.save(update_fields=['error_message', 'retry_count', 'status', 'updated_at'])
            
            # Fire Failure Event for Orchestrator/Dead Letter Queue handling
            classification_failed.send(sender=self.__class__, document_id=doc.id, error_msg=str(exc))
            raise exc
            
        doc.save(update_fields=['error_message', 'retry_count', 'updated_at'])
        # Retry with exponential backoff and jitter
        import random
        jitter = random.uniform(0, 15)
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries) + jitter)
