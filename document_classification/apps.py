from django.apps import AppConfig


class DocumentClassificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_classification'

    def ready(self):
        import document_classification.services.orchestrator
