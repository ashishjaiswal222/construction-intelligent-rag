from uuid import uuid4
from django.db import models

class GenerationLog(models.Model):
    """
    Audit log of every question asked and every answer given.
    Used for quality review, retraining data, and client reporting.
    """

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    project_id = models.CharField(max_length=50, blank=True, db_index=True)
    user_query = models.TextField()
    generated_answer = models.TextField()
    confidence = models.FloatField(default=0.0)
    answer_grounded = models.BooleanField(default=False)
    needs_fallback = models.BooleanField(default=False)
    chunks_used = models.IntegerField(default=0)
    chunk_ids_used = models.JSONField(default=list)
    filter_used = models.JSONField(default=dict)
    stages_completed = models.JSONField(default=list)
    retrieval_ms = models.IntegerField(default=0)
    generation_ms = models.IntegerField(default=0)
    model_used = models.CharField(max_length=100, default='llama-3.1-8b-instant')
    warning_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    thumbs_up = models.BooleanField(null=True, blank=True)
    ragas_faithfulness = models.FloatField(null=True, blank=True)

    class Meta:
        db_table = 'rag_generation_log'
        indexes = [
            models.Index(fields=['project_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['answer_grounded']),
            models.Index(fields=['project_id', 'created_at']),
        ]
