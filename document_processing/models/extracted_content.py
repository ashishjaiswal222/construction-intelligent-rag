import uuid
from django.db import models
from .page import Page

class ExtractedContent(models.Model):
    class ContentType(models.TextChoices):
        TEXT = 'TEXT', 'Text'
        TABLE = 'TABLE', 'Table'
        DRAWING = 'DRAWING', 'Drawing'
        STAMP = 'STAMP', 'Stamp'
        SIGNATURE = 'SIGNATURE', 'Signature'
        REVISION = 'REVISION', 'Revision'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='extracted_contents')
    content_type = models.CharField(max_length=20, choices=ContentType.choices)
    raw_data = models.JSONField()
    text_preview = models.CharField(max_length=500, blank=True)
    confidence = models.FloatField()
    sequence_order = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.content_type} on Page {self.page.page_number} (seq: {self.sequence_order})"
