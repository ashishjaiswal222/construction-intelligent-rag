import uuid
from django.db import models

class RefinedContent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page_id = models.UUIDField(db_index=True)
    raw_text = models.TextField()
    cleaned_text = models.TextField()
    refinement_level = models.CharField(max_length=10)
    layers_applied = models.JSONField(default=list)
    quality_before = models.FloatField()
    quality_after = models.FloatField()
    quality_delta = models.FloatField()
    semantic_validation_used = models.BooleanField(default=False)
    passed_quality_gate = models.BooleanField(default=False)
    needs_human_review = models.BooleanField(default=False)
    refinement_flags = models.JSONField(default=list)
    processing_ms = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refined_content'
        indexes = [
            models.Index(fields=['page_id']),
            models.Index(fields=['needs_human_review']),
            models.Index(fields=['passed_quality_gate']),
        ]

    def __str__(self):
        return f"Refined Content for Page {self.page_id}"
