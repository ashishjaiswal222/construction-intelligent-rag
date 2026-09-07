from django.urls import path
from .views import GenerateView, GenerateDebugView, GenerateAuditView, GenerateHealthView, GenerateFeedbackView

urlpatterns = [
    path('generate/', GenerateView.as_view(), name='generate'),
    path('generate/debug/', GenerateDebugView.as_view(), name='generate-debug'),
    path('generate/audit/', GenerateAuditView.as_view(), name='generate-audit'),
    path('generate/health/', GenerateHealthView.as_view(), name='generate-health'),
    path('generate/<uuid:pk>/feedback/', GenerateFeedbackView.as_view(), name='generate-feedback'),
]
