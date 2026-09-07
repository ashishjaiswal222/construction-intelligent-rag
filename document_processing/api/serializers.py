from rest_framework import serializers
from document_processing.models import ProcessingJob, Page, OCRResult, ExtractedContent

class ProcessingJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingJob
        fields = '__all__'

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'

class OCRResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = OCRResult
        fields = '__all__'

class ExtractedContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtractedContent
        fields = '__all__'
