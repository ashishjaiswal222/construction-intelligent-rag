from django.urls import path
from document_retrieval.api.views import RetrievalQueryView, RetrievalQueryDebugView, RetrievalHealthView

urlpatterns = [
    path('query/', RetrievalQueryView.as_view(), name='retrieval-query'),
    path('query/debug/', RetrievalQueryDebugView.as_view(), name='retrieval-query-debug'),
    path('health/', RetrievalHealthView.as_view(), name='retrieval-health'),
]
