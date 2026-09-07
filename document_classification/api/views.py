from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .serializers import DocumentUploadSerializer, DocumentSerializer, ReviewTaskSerializer
from ..models.document import Document
from ..models.review import ReviewTask
from ..tasks.classify_document import classify_document_task

class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/
    Uploads a document, creates a record, and triggers async classification.
    """
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files')
        project_id = request.data.get('project_id')
        
        if project_id and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                if not request.user.has_project_access(project_id):
                    return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({"error": f"Invalid project ID: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Fallback to single file if 'file' is used instead of 'files'
        if not files and 'file' in request.FILES:
            files = [request.FILES['file']]

        if not files:
            return Response({"error": "No files provided."}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        uploaded_count = 0

        for f in files:
            serializer = DocumentUploadSerializer(data={'file': f, 'project_id': project_id})
            if serializer.is_valid():
                document, created = serializer.save()
                
                if created or document.status != 'indexed':
                    # Document is either new, failed, or stuck in processing.
                    # By re-triggering classification, the pipeline will overwrite old data
                    # and ensure the document reaches the indexed state.
                    classify_document_task.delay(doc_id=str(document.id))
                    results.append({
                        "doc_id": str(document.id),
                        "filename": f.name,
                        "status": "queued",
                        "size_mb": round(f.size / (1024 * 1024), 2)
                    })
                    uploaded_count += 1
                else:
                    results.append({
                        "doc_id": str(document.id),
                        "filename": f.name,
                        "status": "duplicate",
                        "reason": "Document already exists and is fully indexed",
                        "existing_id": str(document.id),
                        "size_mb": round(f.size / (1024 * 1024), 2)
                    })
            else:
                results.append({
                    "filename": f.name,
                    "status": "rejected",
                    "reason": str(serializer.errors.get('file', ['Invalid file'])[0]),
                    "size_mb": round(f.size / (1024 * 1024), 2)
                })

        return Response({
            "uploaded": uploaded_count,
            "results": results
        }, status=status.HTTP_200_OK)

class DocumentListView(APIView):
    """
    GET /api/documents/
    List all documents, optionally filtered by project_id.
    """
    def get(self, request, *args, **kwargs):
        project_id = request.query_params.get('project_id')
        documents = Document.objects.all()
        
        if project_id:
            if hasattr(request, 'user') and request.user.is_authenticated:
                try:
                    if not request.user.has_project_access(project_id):
                        return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
                except Exception:
                    pass
            documents = documents.filter(project_id=project_id)
        elif hasattr(request, 'user') and request.user.is_authenticated and not request.user.is_superuser:
            # Filter to only documents in projects the user has access to
            from project_management.models import ProjectMembership
            project_ids = ProjectMembership.objects.filter(user=request.user).values_list('project_id', flat=True)
            documents = documents.filter(project_id__in=project_ids)
            
        documents = documents.order_by('-created_at')
        serializer = DocumentSerializer(documents, many=True, context={'request': request})
        return Response({
            "documents": serializer.data,
            "total": documents.count()
        }, status=status.HTTP_200_OK)

class DocumentDetailView(APIView):
    """
    GET /api/documents/{id}/
    Retrieve document details.
    """
    def get(self, request, pk, *args, **kwargs):
        document = get_object_or_404(Document, pk=pk)
        
        if hasattr(request, 'user') and request.user.is_authenticated and document.project_id:
            try:
                if not request.user.has_project_access(document.project_id):
                    return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
            except Exception:
                pass
                
        serializer = DocumentSerializer(document, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        document = get_object_or_404(Document, pk=pk)
        
        if hasattr(request, 'user') and request.user.is_authenticated and document.project_id:
            try:
                if not request.user.has_project_access(document.project_id):
                    return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
            except Exception:
                pass
                
        try:
            import os
            from document_indexing.services.qdrant_index_service import QdrantIndexService
            
            qdrant_path = os.environ.get('QDRANT_PATH', './construction_qdrant_db')
            qdrant_service = QdrantIndexService(qdrant_path)
            qdrant_service.delete_chunks_for_document(str(document.id))
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to delete vectors from Qdrant for {document.id}: {e}")
            
        try:
            from django.apps import apps
            DocumentMetadata = apps.get_model('document_metadata', 'DocumentMetadata')
            ChunkingJob = apps.get_model('document_chunking', 'ChunkingJob')
            DocumentChunk = apps.get_model('document_chunking', 'DocumentChunk')
            IndexingRecord = apps.get_model('document_indexing', 'IndexingRecord')
            FailedIndexingJob = apps.get_model('document_indexing', 'FailedIndexingJob')
            
            doc_id_str = str(document.id)
            DocumentMetadata.objects.filter(document_id=doc_id_str).delete()
            ChunkingJob.objects.filter(document_id=doc_id_str).delete()
            DocumentChunk.objects.filter(document_id=doc_id_str).delete()
            IndexingRecord.objects.filter(document_id=doc_id_str).delete()
            FailedIndexingJob.objects.filter(document_id=doc_id_str).delete()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to cascade delete raw UUID references for {document.id}: {e}")
            
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class DocumentStatusView(APIView):
    """
    GET /api/documents/{id}/status/
    Retrieve just the processing status.
    """
    def get(self, request, pk, *args, **kwargs):
        document = get_object_or_404(Document, pk=pk)
        
        if hasattr(request, 'user') and request.user.is_authenticated and document.project_id:
            try:
                if not request.user.has_project_access(document.project_id):
                    return Response({"error": "Access denied"}, status=status.HTTP_403_FORBIDDEN)
            except Exception:
                pass
                
        return Response({
            "id": document.id,
            "status": document.status,
            "status_display": document.get_status_display(),
            "doc_type": document.doc_type,
            "confidence": document.classification_confidence,
            "error_message": document.error_message
        }, status=status.HTTP_200_OK)

class ReviewQueueView(APIView):
    """
    GET /api/documents/review/
    List all documents pending human review or failed in pipeline.
    """
    def get(self, request, *args, **kwargs):
        tasks = ReviewTask.objects.filter(status='pending').select_related('document').order_by('-created_at')
        review_docs = Document.objects.filter(status__in=['needs_review', 'failed']).order_by('-updated_at')
        
        doc_map = {}
        for task in tasks:
            doc = task.document
            if doc and doc.id not in doc_map:
                doc_map[doc.id] = {
                    "doc_id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status,
                    "doc_type": doc.doc_type,
                    "last_error_stage": "classification" if doc.status == "needs_review" else "ocr",
                    "classification_confidence": doc.classification_confidence,
                    "retry_count": doc.retry_count,
                    "created_at": doc.created_at.isoformat(),
                    "error_message": doc.error_message or task.reason,
                    "needs_human_review_pages": 0
                }

        for doc in review_docs:
            if doc.id not in doc_map:
                doc_map[doc.id] = {
                    "doc_id": str(doc.id),
                    "filename": doc.filename,
                    "status": doc.status,
                    "doc_type": doc.doc_type,
                    "last_error_stage": "classification" if doc.status == "needs_review" else "ocr",
                    "classification_confidence": doc.classification_confidence,
                    "retry_count": doc.retry_count,
                    "created_at": doc.created_at.isoformat(),
                    "error_message": doc.error_message or f"Document in {doc.status} status",
                    "needs_human_review_pages": 0
                }

        return Response({"queue": list(doc_map.values())}, status=status.HTTP_200_OK)

class ReviewActionView(APIView):
    """
    POST /api/documents/<uuid:doc_id>/review-action/
    Admin action to Approve (with optional doc_type override) or Reject a document.
    """
    def post(self, request, pk, *args, **kwargs):
        document = get_object_or_404(Document, pk=pk)
        action = request.data.get('action', '').lower()
        doc_type_override = request.data.get('doc_type')
        doc_subtype_override = request.data.get('doc_subtype')
        
        if action == 'approve':
            if doc_type_override:
                document.doc_type = doc_type_override
            if doc_subtype_override:
                document.doc_subtype = doc_subtype_override
                
            document.status = 'classified'
            document.save()
            
            # Resolve pending ReviewTasks for this document
            ReviewTask.objects.filter(document=document, status='pending').update(status='approved')
            
            # Trigger downstream processing ONLY upon approval!
            from document_processing.tasks.process_document import process_document_task
            process_document_task.delay(str(document.id))
            
            return Response({
                "status": "approved",
                "doc_id": str(document.id),
                "doc_type": document.doc_type,
                "message": f"Document '{document.filename}' approved as '{document.doc_type}' and queued for processing."
            }, status=status.HTTP_200_OK)
            
        elif action == 'reject':
            doc_id_str = str(document.id)
            storage_path = document.storage_path
            
            # 1. Delete vector points from Qdrant and BM25 index
            try:
                import requests
                requests.post("http://127.0.0.1:8000/api/indexing/internal/qdrant/", json={"action": "delete", "document_id": doc_id_str}, timeout=5)
            except Exception:
                pass
                
            try:
                from document_indexing.services.bm25_index_service import BM25IndexService
                bm25 = BM25IndexService.get_instance()
                bm25.load()
                bm25.remove_documents(doc_id_str)
            except Exception:
                pass
                
            # 2. Cascade delete related DB records across apps
            from django.apps import apps
            try:
                DocumentMetadata = apps.get_model('document_metadata', 'DocumentMetadata')
                ChunkingJob = apps.get_model('document_chunking', 'ChunkingJob')
                DocumentChunk = apps.get_model('document_chunking', 'DocumentChunk')
                IndexingRecord = apps.get_model('document_indexing', 'IndexingRecord')
                FailedIndexingJob = apps.get_model('document_indexing', 'FailedIndexingJob')
                LLMUsageLog = apps.get_model('document_classification', 'LLMUsageLog')
                
                DocumentMetadata.objects.filter(document_id=doc_id_str).delete()
                ChunkingJob.objects.filter(document_id=doc_id_str).delete()
                DocumentChunk.objects.filter(document_id=doc_id_str).delete()
                IndexingRecord.objects.filter(document_id=doc_id_str).delete()
                FailedIndexingJob.objects.filter(document_id=doc_id_str).delete()
                LLMUsageLog.objects.filter(document_id=doc_id_str).delete()
            except Exception:
                pass

            ReviewTask.objects.filter(document=document).delete()
            document.delete()
            
            # 3. Delete file from storage disk
            if storage_path and os.path.exists(storage_path):
                try:
                    os.remove(storage_path)
                except Exception:
                    pass

            return Response({
                "status": "rejected",
                "doc_id": doc_id_str,
                "message": "Document rejected and permanently purged from database and index."
            }, status=status.HTTP_200_OK)
            
        else:
            return Response({"error": "Invalid action. Choose 'approve' or 'reject'."}, status=status.HTTP_400_BAD_REQUEST)
