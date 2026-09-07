from uuid import uuid4
from django.db import models

class ChunkingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        PARTIAL = 'PARTIAL', 'Partial'
        AGGREGATING = 'AGGREGATING', 'Aggregating'

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    doc_type = models.CharField(max_length=50, blank=True)
    total_pages = models.IntegerField(default=0)
    chunked_pages = models.IntegerField(default=0)
    failed_pages = models.IntegerField(default=0)
    total_chunks = models.IntegerField(default=0)
    strategy_breakdown = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chunking_job'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['status'])
        ]
