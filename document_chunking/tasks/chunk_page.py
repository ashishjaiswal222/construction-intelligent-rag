import time
import logging
from celery import shared_task
from document_chunking.repositories.chunking_repository import ChunkingRepository
from document_chunking.services.chunking_dispatcher import ChunkingDispatcher
from document_chunking.models.chunking_job import ChunkingJob

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def chunk_page_task(self, page_id: str, job_id: str):
    start = time.time()
    repo = ChunkingRepository()
    
    try:
        # Load job
        job = ChunkingJob.objects.get(id=job_id)
        document_id = str(job.document_id)
        
        # Load refined pages (we only pass page_id, so we fetch just this one)
        refined_pages = repo.get_refined_pages(document_id)
        page_data = next((p for p in refined_pages if p['page_id'] == page_id), None)
        
        if not page_data:
            # Maybe the page didn't pass quality gate. We skip chunking.
            repo.update_job_progress(job_id=job_id, failed_pages=1)
            return {'page_id': page_id, 'status': 'skipped_no_data'}
            
        cleaned_text = page_data['cleaned_text']
        doc_type = page_data['doc_type']
        page_number = page_data['page_number']
        needs_human_review = page_data['needs_human_review']
        
        # Extracted data logic
        extracted_data = None
        if doc_type == 'boq':
            extracted_data = repo.get_extracted_tables(page_id)
        elif doc_type == 'drawing':
            extracted_data = repo.get_drawing_data(page_id)
            
        document_metadata = repo.get_document_context(document_id)
        
        dispatcher = ChunkingDispatcher()
        chunks = dispatcher.dispatch(
            doc_type=doc_type,
            cleaned_text=cleaned_text,
            page_id=page_id,
            page_number=page_number,
            document_metadata=document_metadata,
            extracted_data=extracted_data
        )
        
        if needs_human_review:
            for chunk in chunks:
                chunk.metadata['needs_review'] = True
                
        # Save chunks
        repo.save_chunks(chunks=chunks, job=job, document_id=document_id, page_id=page_id)
        
        # Update progress
        repo.update_job_progress(job_id=job_id, chunked_pages=1, total_chunks=len(chunks))
        
        processing_ms = int((time.time() - start) * 1000)
        
        logger.info(
            "page_chunked",
            extra={
                'event': 'page_chunked',
                'page_id': page_id,
                'doc_type': doc_type,
                'strategy_used': chunks[0].strategy_used if chunks else 'none',
                'chunks_produced': len(chunks),
                'processing_ms': processing_ms,
            }
        )
        
        return {'page_id': page_id, 'status': 'success'}
        
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            repo.update_job_progress(job_id=job_id, failed_pages=1)
            logger.error(f"Chunk page task failed permanently for page {page_id}: {exc}")
            return {'page_id': page_id, 'status': 'failed'}
