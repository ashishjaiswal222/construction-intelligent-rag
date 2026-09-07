from django.urls import path
from .views import RefinementSummaryView, RefinedPageView, RefinementReviewQueueView

urlpatterns = [
    path('<str:document_id>/summary/', RefinementSummaryView.as_view(), name='refinement-summary'),
    path('pages/<str:page_id>/', RefinedPageView.as_view(), name='refined-page'),
    path('<str:document_id>/review-queue/', RefinementReviewQueueView.as_view(), name='refinement-review-queue'),
]
