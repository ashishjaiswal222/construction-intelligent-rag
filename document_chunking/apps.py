from django.apps import AppConfig

class DocumentChunkingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_chunking'

    def ready(self):
        import document_chunking.signals
