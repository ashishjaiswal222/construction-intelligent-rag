from django.apps import AppConfig


class DocumentRefinementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_refinement'

    def ready(self):
        import document_refinement.signals
