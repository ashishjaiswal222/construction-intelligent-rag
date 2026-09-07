from django.dispatch import Signal, receiver
import logging
from uuid import UUID

logger = logging.getLogger(__name__)

# Signal emitted when Phase 3 is completely done
refinement_completed = Signal() # provides_args=["document_id"]

# Connect to Phase 2 processing_completed signal
try:
    from document_processing.signals import processing_completed
    
    @receiver(processing_completed)
    def start_refinement(sender, document_id: UUID, **kwargs):
        logger.info(f"Received processing_completed for document {document_id}. Triggering refinement layer.")
        from document_refinement.tasks.refine_document import refine_document_task
        refine_document_task.delay(str(document_id))
        
except ImportError:
    logger.warning("Could not import document_processing.signals. Ensure Phase 2 is installed.")
