import logging
from django.dispatch import receiver
from shared.events import classification_completed, classification_failed
from ..models.document import Document
from ..models.review import ReviewTask, ReviewStatus

logger = logging.getLogger(__name__)

@receiver(classification_completed)
def handle_classification_completed(sender, document_id, **kwargs):
    """
    Orchestrates the next step in the pipeline based on classification results.
    """
    logger.info(f"Orchestrator received classification_completed for document {document_id}")
    
    try:
        doc = Document.objects.get(id=document_id)
        
        # If confidence is too low, route to Human Review Queue
        if doc.classification_confidence is not None and doc.classification_confidence < 0.75:
            ReviewTask.objects.create(
                document=doc,
                reason=f"Low classification confidence: {doc.classification_confidence}",
                status=ReviewStatus.PENDING
            )
            logger.info(f"Routed document {document_id} to ReviewTask queue.")
            return

        # Future Pipeline Stages (OCR, Chunking)
        # e.g., if doc.doc_type == 'drawing':
        #    vision_extraction_task.delay(doc_id=doc.id)
        # else:
        #    ocr_document_task.delay(doc_id=doc.id, strategy=doc.ocr_strategy)
        
        logger.info(f"Document {document_id} ready for next pipeline stage (Not Implemented yet).")
        
    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found during orchestration.")

@receiver(classification_failed)
def handle_classification_failed(sender, document_id, error_msg, **kwargs):
    """
    Handles complete failure of the classification stage.
    """
    logger.error(f"Orchestrator received classification_failed for document {document_id}: {error_msg}")
    
    try:
        doc = Document.objects.get(id=document_id)
        ReviewTask.objects.create(
            document=doc,
            reason=f"Classification failed completely: {error_msg}",
            status=ReviewStatus.PENDING
        )
        logger.info(f"Routed failed document {document_id} to ReviewTask queue.")
    except Document.DoesNotExist:
        pass
