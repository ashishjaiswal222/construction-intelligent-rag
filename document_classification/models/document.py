import uuid
from django.db import models
from .choices import DocumentStatus, DocumentType

class DocumentFingerprint(models.Model):
    hash = models.CharField(max_length=64, primary_key=True, help_text="SHA256 of file content")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'document_fingerprints'

class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Using CharField for project_id to decouple from a specific Project model in Phase-1
    project_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    
    fingerprint = models.ForeignKey(DocumentFingerprint, on_delete=models.PROTECT, null=True, related_name='documents')
    
    filename = models.CharField(max_length=500)
    original_filename = models.CharField(max_length=500)
    file_hash = models.CharField(max_length=64, unique=True, db_index=True)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    mime_type = models.CharField(max_length=100)
    storage_path = models.CharField(max_length=1000)
    page_count = models.IntegerField(null=True, blank=True)

    # Classification & Confidences
    doc_type = models.CharField(max_length=50, choices=DocumentType.choices, default=DocumentType.UNKNOWN)
    doc_subtype = models.CharField(max_length=100, blank=True)
    
    classification_confidence = models.FloatField(null=True, blank=True)
    layout_confidence = models.FloatField(null=True, blank=True)
    ocr_confidence = models.FloatField(null=True, blank=True)
    
    classifier_used = models.CharField(max_length=50, blank=True)

    # Processing Status
    status = models.CharField(max_length=30, choices=DocumentStatus.choices, default=DocumentStatus.QUEUED)
    
    # Granular Flags extracted from LLM/Heuristics
    has_tables = models.BooleanField(default=False)
    has_images = models.BooleanField(default=False)
    has_drawings = models.BooleanField(default=False)
    has_handwriting = models.BooleanField(default=False)
    
    contains_stamp = models.BooleanField(default=False)
    contains_signature = models.BooleanField(default=False)
    contains_revision_block = models.BooleanField(default=False)
    contains_title_block = models.BooleanField(default=False)
    contains_grid_reference = models.BooleanField(default=False)
    
    language = models.CharField(max_length=20, default='en')

    # Audit & Error Handling
    error_message = models.TextField(blank=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'document_records'
        indexes = [
            models.Index(fields=['project_id', 'doc_type']),
            models.Index(fields=['status']),
            models.Index(fields=['file_hash']),
        ]

    def __str__(self):
        return f'{self.get_doc_type_display()} | {self.filename[:50]}'
