import uuid
from django.db import models
from .document import Document

class ReviewStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Review'
    IN_PROGRESS = 'in_progress', 'Review in Progress'
    RESOLVED = 'resolved', 'Resolved'

class ReviewTask(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='review_tasks')
    
    reason = models.TextField(help_text="Reason why this document requires human review")
    status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.PENDING)
    
    assigned_to = models.CharField(max_length=100, blank=True, help_text="User ID of the reviewer")
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'review_tasks'
        ordering = ['-created_at']
