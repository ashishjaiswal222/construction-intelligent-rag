from django.dispatch import Signal, receiver
from document_refinement.signals import refinement_completed
from document_chunking.tasks.chunk_document import chunk_document_task

chunking_completed = Signal()

@receiver(refinement_completed)
def handle_refinement_completed(sender, **kwargs):
    document_id = kwargs.get('document_id')
    if document_id:
        chunk_document_task.delay(str(document_id))
