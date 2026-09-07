import os
import time
import logging
from celery import shared_task
from django.db import transaction
from document_indexing.signals import indexing_completed
from document_indexing.repositories.indexing_repository import IndexingRepository
from document_indexing.services.text_preprocessor import TextPreprocessor
from document_indexing.services.embedding_service import EmbeddingService
from document_indexing.services.qdrant_index_service import QdrantIndexService
from document_indexing.services.bm25_index_service import BM25IndexService
from document_indexing.schemas.chunk_payload import ChunkPayload
from document_indexing.models.failed_indexing_job import FailedIndexingJob

logger = logging.getLogger(__name__)

COLLECTION_NAME = 'construction_docs'

@shared_task(bind=True, max_retries=3, default_retry_delay=60, rate_limit='15/m')
def embed_and_index_task(self, document_id: str, had_version_update: bool = False):
    """
    Triggered by metadata_extracted signal.
    Preprocesses, embeds, and indexes all chunks for a document.
    """
    start = time.time()
    repository = IndexingRepository()
    
    from document_classification.models.document import Document
    from document_classification.models.choices import DocumentStatus
    
    # Dependencies
    api_key = os.environ.get('GEMINI_API_KEY', 'placeholder')
    persist_dir = os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db')
    
    # Step 1: Mark processing
    try:
        repository.mark_status(document_id, 'processing')
        Document.objects.filter(id=document_id).update(status=DocumentStatus.EMBEDDING)
    except Exception as e:
        logger.error(f"Failed to mark processing for {document_id}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    try:
        # Step 2: Load chunks
        chunks_data = repository.get_chunks_for_document(document_id)
        if not chunks_data:
            logger.warning(f"No is_current=True chunks found for document {document_id}")
            repository.mark_status(document_id, 'indexed')
            Document.objects.filter(id=document_id).update(status=DocumentStatus.INDEXED)
            indexing_completed.send(
                sender=None,
                document_id=document_id,
                chunks_indexed=0,
                had_version_update=had_version_update,
            )
            return

        # Step 3: Load metadata
        metadata = repository.get_metadata_for_document(document_id)
        if metadata is None:
            metadata = {'is_current': True}

        # Step 4: Load doc_type
        doc_type = repository.get_doc_type(document_id)

        # Step 5: Build payloads
        payloads = []
        for chunk in chunks_data:
            combined = {
                'chunk_id': str(chunk['id']),
                'document_id': document_id,
                'collection_name': COLLECTION_NAME,
                'raw_text': chunk['chunk_text'],
                'chunk_sequence': chunk['chunk_sequence'],
                'total_chunks': chunk['total_chunks'],
                'doc_type': doc_type,
                **metadata
            }
            payload = ChunkPayload(**combined)
            payloads.append(payload)

        # Step 6: Preprocess and Hash
        preprocessor = TextPreprocessor()
        total_tokens = 0
        import hashlib
        for payload in payloads:
            payload.preprocessed_text = preprocessor.preprocess(payload.raw_text, doc_type)
            # Calculate MD5 for caching
            payload.content_hash = hashlib.md5(payload.preprocessed_text.encode('utf-8')).hexdigest()
            total_tokens += preprocessor.estimate_tokens(payload.preprocessed_text)
            
        avg_tokens_per_chunk = float(total_tokens) / len(payloads) if payloads else 0.0

        # Services
        qdrant_service = QdrantIndexService(persist_dir, api_key)
        bm25_service = BM25IndexService.get_instance()
        embedding_service = EmbeddingService(api_key)

        # Token Optimization: Fetch existing vectors to skip re-embedding
        existing_data = qdrant_service.get_existing_hashes(document_id)
        
        payloads_to_embed = []
        cached_embeddings = {}
        
        for p in payloads:
            existing = existing_data.get(p.chunk_id)
            if existing and existing['hash'] == p.content_hash:
                # Text hasn't changed, reuse the vector!
                cached_embeddings[p.chunk_id] = existing['vector']
            else:
                payloads_to_embed.append(p)

        # Step 7: Clean up old vectors from Qdrant/BM25 before inserting new ones
        # This prevents duplicate RAG results when re-processing documents.
        # Done AFTER fetching existing vectors so token optimization still works!
        qdrant_service.delete_chunks_for_document(document_id)
        bm25_service.remove_documents(document_id)

        try:
            # Step 8: Embed ONLY the new/changed chunks
            new_embeddings = []
            rate_limit_waits = 0
            model_used = 'gemini'
            
            if payloads_to_embed:
                new_embeddings, rate_limit_waits, model_used = embedding_service.embed_chunks_batched(
                    payloads_to_embed, document_id
                )
            elif cached_embeddings:
                first_cached_id = list(cached_embeddings.keys())[0]
                model_used = existing_data[first_cached_id].get('model_used', 'gemini')
                
            # Reconstruct the full list of embeddings in the correct order
            final_embeddings = []
            new_idx = 0
            for p in payloads:
                if p.chunk_id in cached_embeddings:
                    final_embeddings.append(cached_embeddings[p.chunk_id])
                else:
                    final_embeddings.append(new_embeddings[new_idx])
                    new_idx += 1

            # Step 9-11: Upsert, Add to BM25, Save Record atomically
            with transaction.atomic():
                chunks_indexed = qdrant_service.upsert_chunks(payloads, final_embeddings, model_used=model_used)
                bm25_service.add_documents(payloads)
                
                processing_ms = int((time.time() - start) * 1000)
                repository.save_indexing_record(
                    document_id=document_id,
                    status='indexed',
                    chunks_indexed=chunks_indexed,
                    chunks_failed=0,
                    had_version_update=had_version_update,
                    embedding_model=model_used,
                    avg_tokens_per_chunk=avg_tokens_per_chunk,
                    processing_ms=processing_ms,
                    rate_limit_waits=rate_limit_waits,
                )
                Document.objects.filter(id=document_id).update(status=DocumentStatus.INDEXED)
                
            # Step 12: Fire completion signal
            indexing_completed.send(
                sender=IndexingRepository,
                document_id=document_id,
                chunks_indexed=chunks_indexed,
                had_version_update=had_version_update
            )
            
            logger.info({
                'event': 'indexing_completed',
                'document_id': document_id,
                'chunks_indexed': chunks_indexed,
                'processing_ms': processing_ms,
                'model_used': model_used
            })
            
        except Exception as embed_err:
            logger.error(f"Failed to embed/index document {document_id}. Sending to DLQ. Error: {str(embed_err)}")
            FailedIndexingJob.objects.create(
                document_id=document_id,
                error_message=str(embed_err),
                payload=[p.model_dump() for p in payloads]
            )
            repository.mark_status(document_id, 'failed')
            Document.objects.filter(id=document_id).update(status=DocumentStatus.FAILED)
            from shared.reliability.dead_letter import handle_dead_letter
            handle_dead_letter.delay(document_id, str(embed_err), 'embedding')

    except Exception as e:
        logger.error(f"Database or execution error indexing document {document_id}: {str(e)}")
        repository.mark_status(document_id, 'failed')
        Document.objects.filter(id=document_id).update(status=DocumentStatus.FAILED)
        FailedIndexingJob.objects.create(
            document_id=document_id,
            error_message=str(e),
            payload=None
        )
        import random
        jitter = random.uniform(0, 15)
        try:
            raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries) + jitter)
        except self.MaxRetriesExceededError:
            from shared.reliability.dead_letter import handle_dead_letter
            handle_dead_letter.delay(document_id, str(e), 'indexing')
