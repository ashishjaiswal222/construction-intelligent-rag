from django.apps import AppConfig

class DocumentMetadataConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_metadata'

    def ready(self):
        # Register signals
        from document_chunking.signals import chunking_completed
        from document_metadata.tasks.extract_metadata_task import extract_metadata_task

        def on_chunking_completed(sender, document_id, **kwargs):
            extract_metadata_task.delay(document_id=document_id)

        chunking_completed.connect(on_chunking_completed)
