from django.db import models
from django.utils import timezone

class FailedIndexingJob(models.Model):
    document_id = models.CharField(max_length=255, db_index=True)
    error_message = models.TextField()
    payload = models.JSONField(help_text="The chunk payload or metadata that caused the failure, if available", null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    resolved = models.BooleanField(default=False)

    class Meta:
        db_table = 'document_indexing_failed_job'
        ordering = ['-created_at']

    def __str__(self):
        return f"Failed Indexing: {self.document_id} at {self.created_at}"
