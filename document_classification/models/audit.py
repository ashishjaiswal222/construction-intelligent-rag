import uuid
from django.db import models
from .document import Document
from .prompts import PromptVersion

class DocumentClassificationHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='classification_history')
    prompt_version = models.ForeignKey(PromptVersion, on_delete=models.SET_NULL, null=True, blank=True)
    
    classifier_name = models.CharField(max_length=100)
    raw_response = models.TextField(blank=True, help_text="Raw JSON or text returned by LLM")
    
    doc_type_predicted = models.CharField(max_length=50)
    confidence = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'classification_history'
        ordering = ['-created_at']

class LLMUsageLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='llm_usage', null=True, blank=True)
    
    model_name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)
    
    tokens_in = models.IntegerField(default=0)
    tokens_out = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.000000)
    latency_seconds = models.FloatField(null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'llm_usage_logs'
        ordering = ['-created_at']
