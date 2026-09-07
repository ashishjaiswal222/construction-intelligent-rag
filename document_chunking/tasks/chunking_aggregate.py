import logging
from celery import shared_task
from document_chunking.repositories.chunking_repository import ChunkingRepository
from document_chunking.models.chunking_job import ChunkingJob
from document_chunking.models.document_chunk import DocumentChunk
from django.db.models import Count

logger = logging.getLogger(__name__)

@shared_task
def chunking_aggregate_task(page_results: list, job_id: str, document_id: str):
    repo = ChunkingRepository()
    try:
        job = ChunkingJob.objects.get(id=job_id)
        
        total_chunks = DocumentChunk.objects.filter(chunking_job=job).count()
        
        # Strategy breakdown
        breakdown_query = DocumentChunk.objects.filter(chunking_job=job).values('chunk_type').annotate(count=Count('id'))
        strategy_breakdown = {item['chunk_type']: item['count'] for item in breakdown_query}
        
        if job.chunked_pages == 0:
            status = ChunkingJob.Status.FAILED
        elif job.failed_pages > 0:
            status = ChunkingJob.Status.PARTIAL
        else:
            status = ChunkingJob.Status.COMPLETED
            
        repo.complete_job(job_id=job_id, status=status, total_chunks=total_chunks, strategy_breakdown=strategy_breakdown)
        
        from document_chunking.signals import chunking_completed
        chunking_completed.send(
            sender=__name__,
            document_id=document_id,
            total_chunks=total_chunks,
            strategy_breakdown=strategy_breakdown
        )
        
        logger.info(
            "chunking_completed",
            extra={
                'event': 'chunking_completed',
                'document_id': document_id,
                'job_id': job_id,
                'status': status,
                'total_chunks': total_chunks,
            }
        )
        
        return {'status': 'completed', 'job_id': job_id}
        
    except Exception as exc:
        logger.error(f"Aggregate task failed for job {job_id}: {exc}")
        return {'status': 'failed'}
