from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from document_processing.models import ProcessingJob, Page, OCRResult, ExtractedContent
from document_processing.api.serializers import ProcessingJobSerializer, PageSerializer, OCRResultSerializer, ExtractedContentSerializer
from document_processing.tasks.retry_failed_page import retry_failed_page_task

class ProcessingJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProcessingJob.objects.all()
    serializer_class = ProcessingJobSerializer
    lookup_field = 'document_id'

    @action(detail=True, methods=['get'])
    def pages(self, request, document_id=None):
        job = self.get_object()
        pages = Page.objects.filter(processing_job=job)
        serializer = PageSerializer(pages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry(self, request, document_id=None):
        job = self.get_object()
        failed_pages = Page.objects.filter(processing_job=job, status=Page.Status.FAILED)
        for page in failed_pages:
            retry_failed_page_task.delay(str(page.id))
        return Response({"message": f"Triggered retry for {failed_pages.count()} pages."})

class PageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    @action(detail=True, methods=['get'])
    def content(self, request, pk=None):
        page = self.get_object()
        content = ExtractedContent.objects.filter(page=page)
        serializer = ExtractedContentSerializer(content, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def ocr(self, request, pk=None):
        page = self.get_object()
        try:
            ocr_result = OCRResult.objects.get(page=page)
            serializer = OCRResultSerializer(ocr_result)
            return Response(serializer.data)
        except OCRResult.DoesNotExist:
            return Response({"error": "OCR Result not found"}, status=status.HTTP_404_NOT_FOUND)
