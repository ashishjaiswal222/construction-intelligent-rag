import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)

class DocumentIndexingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'document_indexing'

    def ready(self):
        import document_indexing.signals  # register signal handlers

        from document_indexing.services.bm25_index_service import BM25IndexService
        instance = BM25IndexService.get_instance()
        loaded = instance.load()
        if loaded:
            logger.info('BM25 index loaded from disk on startup')
        else:
            logger.warning('BM25 index not found — will build incrementally as documents are indexed')
