from django.urls import path
from .views import (
    IndexingRecordView,
    ProjectIndexingStatsView,
    CollectionStatsView,
    ReindexDocumentView,
    HealthCheckView,
    InternalQdrantView
)

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='indexing-health'),
    path('collection/stats/', CollectionStatsView.as_view(), name='collection-stats'),
    path('project/<str:project_id>/stats/', ProjectIndexingStatsView.as_view(), name='project-stats'),
    path('<str:document_id>/reindex/', ReindexDocumentView.as_view(), name='reindex-document'),
    path('internal/qdrant/<str:action>/', InternalQdrantView.as_view(), name='internal-qdrant'),
    path('<str:document_id>/', IndexingRecordView.as_view(), name='indexing-record'),
]
