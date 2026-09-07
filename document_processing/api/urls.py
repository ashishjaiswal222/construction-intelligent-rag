from django.urls import path, include
from rest_framework.routers import DefaultRouter
from document_processing.api.views import ProcessingJobViewSet, PageViewSet

router = DefaultRouter()
router.register(r'jobs', ProcessingJobViewSet, basename='processingjob')
router.register(r'pages', PageViewSet, basename='page')

urlpatterns = [
    path('', include(router.urls)),
]
