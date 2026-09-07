from uuid import uuid4
from django.db import models
from document_chunking.models.chunking_job import ChunkingJob

class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    document_id = models.UUIDField(db_index=True)
    chunking_job = models.ForeignKey(ChunkingJob, on_delete=models.CASCADE)
    page_id = models.UUIDField(db_index=True)
    
    is_current = models.BooleanField(default=True, db_index=True)
    doc_type = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    revision = models.CharField(max_length=20, blank=True, null=True)
    
    chunk_index = models.IntegerField()
    chunk_type = models.CharField(max_length=50)
    content = models.TextField()
    metadata = models.JSONField(default=dict)
    char_count = models.IntegerField()
    word_count = models.IntegerField()
    strategy_used = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'document_chunk'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['page_id']),
            models.Index(fields=['chunk_type']),
            models.Index(fields=['document_id', 'chunk_index']),
        ]
        ordering = ['document_id', 'chunk_index']
