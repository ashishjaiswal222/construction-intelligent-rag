from django.urls import path
from .views import (
    DocumentMetadataDetailView,
    CurrentProjectMetadataView,
    ProjectDrawingsView,
    VerifyMetadataView,
    OverrideMetadataView,
    ReviewQueueView
)

urlpatterns = [
    path('queue/', ReviewQueueView.as_view(), name='metadata_queue'),
    path('<uuid:document_id>/', DocumentMetadataDetailView.as_view(), name='metadata_detail'),
    path('project/<str:project_id>/current/', CurrentProjectMetadataView.as_view(), name='project_current_metadata'),
    path('project/<str:project_id>/drawings/', ProjectDrawingsView.as_view(), name='project_drawings'),
    path('<uuid:document_id>/verify/', VerifyMetadataView.as_view(), name='verify_metadata'),
    path('<uuid:document_id>/override/', OverrideMetadataView.as_view(), name='override_metadata'),
]
