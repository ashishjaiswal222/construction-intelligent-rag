from celery import shared_task, chord
from django.utils import timezone
from document_chunking.repositories.chunking_repository import ChunkingRepository
from document_chunking.tasks.chunk_page import chunk_page_task
from document_chunking.tasks.chunking_aggregate import chunking_aggregate_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def chunk_document_task(self, document_id: str):
    repo = ChunkingRepository()
    
    try:
        document_metadata = repo.get_document_context(document_id)
        if not document_metadata:
            return {'status': 'failed', 'reason': 'Document not found'}
            
        doc_type = document_metadata.get('doc_type', '')
        
        from document_classification.models.document import Document
        from document_classification.models.choices import DocumentStatus
        from document_chunking.models.document_chunk import DocumentChunk
        
        Document.objects.filter(id=document_id).update(status=DocumentStatus.CHUNKING)
        
        # Delete old chunks to prevent duplicates on re-processing
        DocumentChunk.objects.filter(document_id=document_id).delete()
        
        job = repo.create_chunking_job(document_id, doc_type)
        job.started_at = timezone.now()
        job.save()
        
        refined_pages = repo.get_refined_pages(document_id)
        if not refined_pages:
            job.status = job.Status.FAILED
            job.error_message = 'No passed pages found to chunk.'
            job.completed_at = timezone.now()
            job.save()
            return {'status': 'failed', 'reason': 'No pages'}
            
        job.total_pages = len(refined_pages)
        job.save()
        
        tasks = [chunk_page_task.s(page['page_id'], str(job.id)) for page in refined_pages]
        callback = chunking_aggregate_task.s(str(job.id), document_id)
        
        chord(tasks)(callback)
        
        return {'status': 'processing', 'job_id': str(job.id)}
        
    except Exception as exc:
        try:
            self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            return {'status': 'failed'}
