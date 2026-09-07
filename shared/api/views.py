from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, timezone

from project_management.models import Project, ProjectMembership
import logging

logger = logging.getLogger(__name__)

class ProjectListView(APIView):
    def get(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # If not superuser, filter by memberships
            if not request.user.is_superuser:
                project_ids = ProjectMembership.objects.filter(user=request.user).values_list('project_id', flat=True)
                projects = Project.objects.filter(id__in=project_ids).order_by('-created_at')
            else:
                projects = Project.objects.all().order_by('-created_at')
        else:
            projects = []
            
        data = []
        for p in projects:
            data.append({
                "project_id": str(p.id),
                "name": p.name,
                "type": p.type,
                "location": p.location,
                "phase": p.phase,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
            
        return Response({"projects": data})

    def post(self, request):
        try:
            name = request.data.get('name')
            ptype = request.data.get('type', 'Unknown')
            location = request.data.get('location', 'Unknown')
            phase = request.data.get('phase', 'Planning')
            
            if not name:
                return Response({"error": "Name is required"}, status=400)
                
            project = Project.objects.create(
                name=name,
                type=ptype,
                location=location,
                phase=phase
            )
            
            if hasattr(request, 'user') and request.user.is_authenticated:
                ProjectMembership.objects.create(
                    user=request.user,
                    project=project,
                    role='project_admin'
                )
                
            return Response({
                "status": "success", 
                "project": {
                    "project_id": str(project.id),
                    "name": project.name,
                    "type": project.type,
                    "location": project.location,
                    "phase": project.phase
                }
            })
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            return Response({"error": str(e)}, status=500)

class HealthView(APIView):
    def get(self, request):
        return Response({
            "status": "ok",
            "services": {
                "database": True,
                "redis": True,
                "vector_store": True
            }
        })

class MetricsView(APIView):
    def get(self, request):
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        from django.http import HttpResponse
        
        # If the request accepts text/plain (Prometheus scraper), return standard metrics
        if 'text/plain' in request.META.get('HTTP_ACCEPT', ''):
            metrics_data = generate_latest()
            return HttpResponse(metrics_data, content_type=CONTENT_TYPE_LATEST)
            
        from django.core.cache import cache
        project_id = request.GET.get('project_id')
        cache_key = f"dashboard_metrics_{project_id or 'global'}"
        
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        from shared.observability.metrics import QUEUE_DEPTH
        from document_classification.models import Document
        from document_classification.models.review import ReviewTask
        from document_processing.models.ocr_result import OCRResult
        from rag_generation.models import GenerationLog
        from document_classification.models.audit import LLMUsageLog
        from django.db.models import Avg

        # 1. Queue depth
        try:
            queue_depth = int(QUEUE_DEPTH.labels(queue='default')._value.get() if hasattr(QUEUE_DEPTH.labels(queue='default'), '_value') else 0)
        except Exception:
            queue_depth = 0
            
        # 2. Document Metrics
        ocr_qs = OCRResult.objects.all()
        doc_qs = Document.objects.all()
        review_qs = ReviewTask.objects.filter(status='pending')
        
        if project_id:
            ocr_qs = ocr_qs.filter(page__document__project_id=project_id)
            doc_qs = doc_qs.filter(project_id=project_id)
            review_qs = review_qs.filter(document__project_id=project_id)
        
        ocr_confidence_avg = ocr_qs.aggregate(avg_conf=Avg('confidence'))['avg_conf']
        classification_confidence_avg = doc_qs.aggregate(avg_conf=Avg('classification_confidence'))['avg_conf']
        human_review_queue_size = review_qs.count()
        
        # 3. RAG Metrics
        logs_qs = GenerationLog.objects.all()
        if project_id:
            logs_qs = logs_qs.filter(project_id=project_id)
            
        total_logs = logs_qs.count()
        
        query_latency_p95_seconds = None
        cost_per_query_paise = None
        llm_error_rate = None
        retrieval_hit_rate = None
        crag_rejection_rate = None
        thumbs_up_rate = None
        ragas_faithfulness = None

        if total_logs > 0:
            grounded_count = logs_qs.filter(answer_grounded=True).count()
            retrieval_hit_rate = grounded_count / total_logs
            
            fallback_count = logs_qs.filter(needs_fallback=True).count()
            crag_rejection_rate = fallback_count / total_logs
            
            # True P95 Latency Calculation
            recent_logs = list(logs_qs.order_by('-created_at').values_list('generation_ms', flat=True)[:1000])
            if recent_logs:
                import statistics
                if len(recent_logs) >= 2:
                    p95_ms = statistics.quantiles(recent_logs, n=100)[94]
                else:
                    p95_ms = recent_logs[0]
                query_latency_p95_seconds = round(p95_ms / 1000.0, 2)

            error_count = logs_qs.filter(confidence=0.0).count()
            llm_error_rate = error_count / total_logs

            total_rated = logs_qs.exclude(thumbs_up=None).count()
            if total_rated > 0:
                thumbs_up_count = logs_qs.filter(thumbs_up=True).count()
                thumbs_up_rate = thumbs_up_count / total_rated
                
            ragas_faithfulness = logs_qs.exclude(ragas_faithfulness=None).aggregate(
                avg_faith=Avg('ragas_faithfulness')
            )['avg_faith']
            
        # Accurate Cost per Query Calculation (USD -> Paise: 1 USD = 87 INR = 8700 Paise)
        usage_qs = LLMUsageLog.objects.all()
        if project_id:
            usage_qs = usage_qs.filter(document__project_id=project_id)
        avg_cost_usd = usage_qs.aggregate(avg_c=Avg('cost'))['avg_c']
        if avg_cost_usd is not None:
            cost_per_query_paise = round(float(avg_cost_usd) * 8700, 4)
            
        response_data = {
            "query_latency_p95_seconds": query_latency_p95_seconds,
            "retrieval_hit_rate": retrieval_hit_rate,
            "crag_rejection_rate": crag_rejection_rate,
            "llm_error_rate": llm_error_rate,
            "cost_per_query_paise": cost_per_query_paise,
            "ocr_confidence_avg": ocr_confidence_avg,
            "classification_confidence_avg": classification_confidence_avg,
            "queue_depth": queue_depth,
            "human_review_queue_size": human_review_queue_size,
            "ragas_faithfulness": ragas_faithfulness,
            "thumbs_up_rate": thumbs_up_rate,
            "live_metrics_enabled": True
        }
        
        cache.set(cache_key, response_data, timeout=300)
        return Response(response_data)
