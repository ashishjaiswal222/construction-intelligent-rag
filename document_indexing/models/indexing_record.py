import uuid
from django.db import models

class IndexingRecord(models.Model):

    STATUS_CHOICES = [
        ('pending',    'Pending'),
        ('processing', 'Processing'),
        ('indexed',    'Indexed'),
        ('failed',     'Failed'),
        ('reindexed',  'Reindexed after version update'),
    ]

    # PRIMARY KEY
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # LINK (UUID only - no FK across apps)
    document_id = models.UUIDField(unique=True, db_index=True)

    # INDEXING STATE
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    collection_name = models.CharField(max_length=100, blank=True)
    chunks_indexed = models.IntegerField(default=0)
    chunks_failed = models.IntegerField(default=0)
    had_version_update = models.BooleanField(default=False)

    # EMBEDDING METADATA
    embedding_model = models.CharField(max_length=100, default='models/text-embedding-004')
    embedding_dims = models.IntegerField(default=768)
    avg_tokens_per_chunk = models.FloatField(null=True)

    # PERFORMANCE
    processing_ms = models.IntegerField(null=True)
    rate_limit_waits = models.IntegerField(default=0)

    # AUDIT
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    error_message = models.TextField(blank=True)

    class Meta:
        db_table = 'document_indexing_record'
        indexes = [
            models.Index(fields=['document_id']),
            models.Index(fields=['status']),
            models.Index(fields=['collection_name', 'status']),
        ]
