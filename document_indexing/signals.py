from django.dispatch import Signal, receiver
from document_metadata.signals import metadata_extracted

# Outgoing signal
indexing_completed = Signal() # kwargs: document_id, chunks_indexed, collection_name, had_version_update

@receiver(metadata_extracted)
def trigger_embed_and_index(sender, document_id, metadata_confidence, is_current, has_version_chain_update, **kwargs):
    from document_indexing.tasks.embed_and_index_task import embed_and_index_task
    
    # Always dispatch regardless of metadata_confidence
    embed_and_index_task.delay(
        document_id=str(document_id),
        had_version_update=has_version_chain_update
    )
