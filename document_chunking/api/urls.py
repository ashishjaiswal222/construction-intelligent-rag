from django.urls import path
from document_chunking.api.views import (
    get_chunking_job,
    get_document_chunks,
    get_chunking_stats,
    retry_chunking_job
)

urlpatterns = [
    path('jobs/<uuid:document_id>/', get_chunking_job, name='chunking-job-detail'),
    path('documents/<uuid:document_id>/chunks/', get_document_chunks, name='document-chunks-list'),
    path('documents/<uuid:document_id>/stats/', get_chunking_stats, name='document-chunking-stats'),
    path('jobs/<uuid:document_id>/retry/', retry_chunking_job, name='retry-chunking-job'),
]
