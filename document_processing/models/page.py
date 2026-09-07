import uuid
from django.db import models
from document_classification.models import Document
from .processing_job import ProcessingJob

class Page(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PROCESSING = 'PROCESSING', 'Processing'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        RETRYING = 'RETRYING', 'Retrying'
        NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Review'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    processing_job = models.ForeignKey(ProcessingJob, on_delete=models.CASCADE, related_name='pages')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='processed_pages')
    page_number = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    strategy_used = models.CharField(max_length=50, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    char_count = models.IntegerField(default=0)
    quality_score = models.FloatField(null=True, blank=True)
    
    contains_tables = models.BooleanField(default=False)
    contains_handwriting = models.BooleanField(default=False)
    contains_drawing = models.BooleanField(default=False)
    contains_stamp = models.BooleanField(default=False)
    contains_signature = models.BooleanField(default=False)
    contains_revision_block = models.BooleanField(default=False)
    contains_title_block = models.BooleanField(default=False)
    
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    
    refinement_level = models.CharField(max_length=10, blank=True, default='')
    layers_to_run = models.JSONField(default=list)

    def __str__(self):
        return f"Page {self.page_number} for Job {self.processing_job_id}"
