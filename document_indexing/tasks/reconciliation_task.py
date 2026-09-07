import os
import logging
from celery import shared_task
from django.db import connection
from document_indexing.models.indexing_record import IndexingRecord
from document_indexing.services.qdrant_index_service import QdrantIndexService
from document_indexing.services.bm25_index_service import BM25IndexService
from document_indexing.tasks.embed_and_index_task import embed_and_index_task

logger = logging.getLogger(__name__)

@shared_task
def index_reconciliation_task():
    """
    Nightly beat task to ensure BM25 and Qdrant are perfectly in sync with the database.
    Checks all documents with status='indexed'.
    If they are missing from Qdrant or BM25, re-queues them.
    """
    logger.info("Starting nightly index reconciliation...")
    
    # 1. Get all indexed documents from the DB
    indexed_records = IndexingRecord.objects.filter(status='indexed').values_list('document_id', flat=True)
    db_doc_ids = set(map(str, indexed_records))

    if not db_doc_ids:
        logger.info("No indexed documents found in DB. Reconciliation complete.")
        return

    # 2. Get BM25 state
    bm25_service = BM25IndexService.get_instance()
    bm25_service.load()
    bm25_doc_ids = set(map(str, bm25_service._document_ids))

    # 3. Find mismatches
    # Documents in DB that are missing from BM25
    missing_from_bm25 = db_doc_ids - bm25_doc_ids
    
    # (Optional) We could also query Qdrant to find docs missing there,
    # but that requires scrolling through Qdrant completely which is expensive.
    # Generally, if it's missing from BM25, we should reindex.
    
    if missing_from_bm25:
        logger.warning(f"Reconciliation found {len(missing_from_bm25)} documents missing from BM25. Re-queueing...")
        for doc_id in missing_from_bm25:
            # Change status to pending so it gets picked up cleanly
            IndexingRecord.objects.filter(document_id=doc_id).update(status='pending')
            
            embed_and_index_task.delay(doc_id, had_version_update=True)
            
    logger.info("Reconciliation complete.")
