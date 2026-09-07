import uuid
from django.db import models
from .page import Page

class OCRResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.OneToOneField(Page, on_delete=models.CASCADE, related_name='ocr_result')
    raw_text = models.TextField()
    cleaned_text = models.TextField()
    strategy_used = models.CharField(max_length=50)
    confidence = models.FloatField()
    char_count = models.IntegerField()
    word_count = models.IntegerField()
    processing_ms = models.IntegerField()
    has_handwriting = models.BooleanField(default=False)
    handwriting_segments = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OCRResult for Page {self.page.page_number}"
