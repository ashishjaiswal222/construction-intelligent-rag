from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from document_classification.models.document import Document
from document_classification.models.choices import DocumentStatus
from document_processing.models.processing_job import ProcessingJob
from document_chunking.models.chunking_job import ChunkingJob
from document_indexing.models.indexing_record import IndexingRecord

import logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=ProcessingJob)
def sync_processing_job_status(sender, instance, created, **kwargs):
    """
    Syncs the Document status when a ProcessingJob changes.
    ProcessingJob.Status -> Document.status
    """
    try:
        doc = instance.document
        if instance.status == 'COMPLETED':
            doc.status = DocumentStatus.OCR_PROCESSING
            # Assuming OCR is done, but the master status should reflect it passed OCR. 
            # Wait, the next stage is refinement/chunking. Let's just set it to CHUNKING as it progresses.
            doc.save(update_fields=['status'])
        elif instance.status == 'FAILED':
            doc.status = DocumentStatus.FAILED
            doc.save(update_fields=['status'])
    except Exception as e:
        logger.error(f"Failed to sync processing job status for {instance.id}: {e}")

@receiver(post_save, sender=ChunkingJob)
def sync_chunking_job_status(sender, instance, created, **kwargs):
    """
    Syncs the Document status when a ChunkingJob changes.
    ChunkingJob.Status -> Document.status
    """
    try:
        doc = Document.objects.get(id=instance.document_id)
        if instance.status == 'PROCESSING':
            doc.status = DocumentStatus.CHUNKING
            doc.save(update_fields=['status'])
        elif instance.status == 'COMPLETED':
            doc.status = DocumentStatus.EMBEDDING
            doc.save(update_fields=['status'])
        elif instance.status == 'FAILED':
            doc.status = DocumentStatus.FAILED
            doc.save(update_fields=['status'])
    except Document.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Failed to sync chunking job status for {instance.id}: {e}")

@receiver(post_save, sender=IndexingRecord)
def sync_indexing_record_status(sender, instance, created, **kwargs):
    """
    Syncs the Document status when an IndexingRecord changes.
    IndexingRecord.Status -> Document.status
    """
    try:
        doc = Document.objects.get(id=instance.document_id)
        if instance.status == 'processing':
            doc.status = DocumentStatus.EMBEDDING
            doc.save(update_fields=['status'])
        elif instance.status == 'indexed':
            doc.status = DocumentStatus.INDEXED
            doc.save(update_fields=['status'])
        elif instance.status == 'failed':
            doc.status = DocumentStatus.FAILED
            doc.save(update_fields=['status'])
    except Document.DoesNotExist:
        pass
    except Exception as e:
        logger.error(f"Failed to sync indexing record status for {instance.id}: {e}")
