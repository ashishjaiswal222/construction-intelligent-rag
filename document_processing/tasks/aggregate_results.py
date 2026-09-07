from celery import shared_task
from django.utils import timezone
from uuid import UUID
from document_processing.repositories.processing_repository import ProcessingRepository
from document_processing.repositories.page_repository import PageRepository
from document_processing.models import ProcessingJob, Page

@shared_task
def aggregate_results_task(results, job_id: str):
    proc_repo = ProcessingRepository()
    page_repo = PageRepository()
    
    pages = page_repo.get_pages_by_job(UUID(job_id))
    
    completed = 0
    failed = 0
    strategy_breakdown = {}
    
    for page in pages:
        if page.status == Page.Status.COMPLETED:
            completed += 1
            strategy = page.strategy_used or "unknown"
            strategy_breakdown[strategy] = strategy_breakdown.get(strategy, 0) + 1
        elif page.status == Page.Status.FAILED:
            failed += 1
            
    # Write strategy_breakdown to ProcessingJob.processing_meta
    meta = {
        "strategy_breakdown": strategy_breakdown,
        "completed_pages": completed,
        "failed_pages": failed,
        "total_pages": len(pages)
    }
    proc_repo.update_meta(UUID(job_id), meta)
    
    # Set ProcessingJob.status = COMPLETED or PARTIAL
    status = ProcessingJob.Status.COMPLETED
    if failed > 0:
        if completed > 0:
            status = ProcessingJob.Status.PARTIAL
        else:
            status = ProcessingJob.Status.FAILED
            
    proc_repo.update_status(UUID(job_id), status)
    
    # Set ProcessingJob.completed_at = now()
    # ProcessingRepository doesn't have an update_completed_at method yet, so we update it directly or add to repo
    # Let's use the ORM directly for this specific field or add a repo method. The prompt says "no ORM in services", this is a task.
    # Tasks can use ORM or repo, but it's cleaner to use ORM if repo misses it, or better, just use ORM.
    ProcessingJob.objects.filter(id=UUID(job_id)).update(completed_at=timezone.now())
    
    # FIRE SIGNAL FOR PHASE 3
    from document_processing.signals import processing_completed
    job = ProcessingJob.objects.get(id=UUID(job_id))
    processing_completed.send(sender=aggregate_results_task, document_id=job.document_id)
    
    return f"Job {job_id} aggregated with status {status}"
