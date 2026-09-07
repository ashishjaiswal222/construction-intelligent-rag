import logging
from django.dispatch import receiver, Signal
from shared.events import classification_completed
from .tasks.process_document import process_document_task

logger = logging.getLogger(__name__)

# Fired when Phase 2 OCR processing is completely done for all pages
processing_completed = Signal()

@receiver(classification_completed)
def on_classification_completed(sender, document_id, doc_type, **kwargs):
    from document_classification.models.document import Document
    try:
        doc = Document.objects.get(id=document_id)
        if doc.doc_type == 'unknown' or doc.status == 'needs_review' or (doc.classification_confidence is not None and doc.classification_confidence < 0.75):
            logger.warning(
                f"[Safeguard] Document '{doc.filename}' (ID: {document_id}) classified as '{doc.doc_type}' "
                f"with confidence {doc.classification_confidence}. Halting downstream OCR/Chunking pipeline "
                f"to save API resources. Sent to Admin Review Queue."
            )
            return
    except Exception as e:
        logger.error(f"Error evaluating classification safeguard for document {document_id}: {e}")

    process_document_task.delay(str(document_id))
