from django.urls import path
from .views import DocumentUploadView, DocumentListView, DocumentDetailView, DocumentStatusView, ReviewQueueView, ReviewActionView

urlpatterns = [
    path('documents/', DocumentListView.as_view(), name='document-list'),
    path('documents/upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('documents/review/', ReviewQueueView.as_view(), name='review-queue'),
    path('documents/<uuid:pk>/review-action/', ReviewActionView.as_view(), name='review-action'),
    path('documents/<uuid:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<uuid:pk>/status/', DocumentStatusView.as_view(), name='document-status'),
]
