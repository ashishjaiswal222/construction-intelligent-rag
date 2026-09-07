from django.urls import path
from .views import ProjectListView, HealthView, MetricsView

urlpatterns = [
    path('projects/', ProjectListView.as_view(), name='projects-list'),
    path('health/', HealthView.as_view(), name='health'),
    path('metrics/kpis/', MetricsView.as_view(), name='metrics-kpis'),
]
