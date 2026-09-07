from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg, Count
import django.db.models as models
from django.shortcuts import get_object_or_404
from uuid import UUID

from document_refinement.models import RefinedContent
from document_refinement.repositories.refinement_repository import RefinementRepository
from .serializers import RefinedContentSerializer

class RefinementSummaryView(APIView):
    def get(self, request, document_id: str):
        # We need to get all page_ids for this document.
        repo = RefinementRepository()
        pages = repo.get_pages_for_document(UUID(document_id))
        page_ids = [p['id'] for p in pages]
        
        refined_qs = RefinedContent.objects.filter(page_id__in=page_ids)
        
        stats = refined_qs.aggregate(
            avg_quality_before=Avg('quality_before'),
            avg_quality_after=Avg('quality_after'),
            avg_quality_delta=Avg('quality_delta'),
            needs_review_count=Count('id', filter=models.Q(needs_human_review=True)),
            semantic_validation_used_count=Count('id', filter=models.Q(semantic_validation_used=True))
        )
        
        # Breakdown by level
        level_counts = dict(refined_qs.values_list('refinement_level').annotate(count=Count('id')))
        
        data = {
            "total_pages": len(pages),
            "refined_pages": refined_qs.count(),
            "needs_review_count": stats.get('needs_review_count', 0),
            "avg_quality_before": stats.get('avg_quality_before') or 0.0,
            "avg_quality_after": stats.get('avg_quality_after') or 0.0,
            "avg_quality_delta": stats.get('avg_quality_delta') or 0.0,
            "level_breakdown": {
                "LIGHT": level_counts.get("LIGHT", 0),
                "MEDIUM": level_counts.get("MEDIUM", 0),
                "HEAVY": level_counts.get("HEAVY", 0),
                "NONE": level_counts.get("NONE", 0),
            },
            "semantic_validation_used_count": stats.get('semantic_validation_used_count', 0)
        }
        
        return Response(data, status=status.HTTP_200_OK)

class RefinedPageView(APIView):
    def get(self, request, page_id: str):
        content = get_object_or_404(RefinedContent, page_id=page_id)
        serializer = RefinedContentSerializer(content)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RefinementReviewQueueView(APIView):
    def get(self, request, document_id: str):
        repo = RefinementRepository()
        pages = repo.get_pages_for_document(UUID(document_id))
        page_ids = [p['id'] for p in pages]
        
        queue = RefinedContent.objects.filter(
            page_id__in=page_ids, 
            needs_human_review=True
        )
        serializer = RefinedContentSerializer(queue, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
 # Add here to satisfy models.Q above
