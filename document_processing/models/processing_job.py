import uuid
from django.db import models
from document_classification.models import Document

class ProcessingJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SPLITTING = 'SPLITTING', 'Splitting'
        PROCESSING = 'PROCESSING', 'Processing'
        AGGREGATING = 'AGGREGATING', 'Aggregating'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        PARTIAL = 'PARTIAL', 'Partial'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='processing_jobs')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_pages = models.IntegerField(default=0)
    processed_pages = models.IntegerField(default=0)
    failed_pages = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    processing_meta = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job {self.id} for Document {self.document_id} ({self.status})"
