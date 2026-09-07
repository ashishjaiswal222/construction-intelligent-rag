import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import connection
from django.shortcuts import get_object_or_404
from document_indexing.models.indexing_record import IndexingRecord
from document_indexing.api.serializers import IndexingRecordSerializer
from document_indexing.services.qdrant_index_service import QdrantIndexService
from document_indexing.services.bm25_index_service import BM25IndexService
from document_indexing.tasks.embed_and_index_task import embed_and_index_task

class IndexingRecordView(APIView):
    def get(self, request, document_id):
        record = get_object_or_404(IndexingRecord, document_id=document_id)
        serializer = IndexingRecordSerializer(record)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ProjectIndexingStatsView(APIView):
    def get(self, request, project_id):
        query = """
            SELECT 
                COUNT(ir.id) as total_documents_indexed,
                COALESCE(SUM(ir.chunks_indexed), 0) as total_chunks_indexed,
                COUNT(CASE WHEN ir.status = 'pending' THEN 1 END) as documents_pending,
                COUNT(CASE WHEN ir.status = 'failed' THEN 1 END) as documents_failed,
                COUNT(CASE WHEN ir.status = 'reindexed' THEN 1 END) as documents_reindexed
            FROM document_indexing_record ir
            JOIN document_metadata dm ON dm.document_id = ir.document_id
            WHERE dm.project_id = %s
        """
        with connection.cursor() as cursor:
            cursor.execute(query, [project_id])
            row = cursor.fetchone()
            
        data = {
            "project_id": project_id,
            "total_documents_indexed": row[0],
            "total_chunks_indexed": row[1],
            "documents_pending": row[2],
            "documents_failed": row[3],
            "documents_reindexed": row[4]
        }
        return Response(data, status=status.HTTP_200_OK)

class CollectionStatsView(APIView):
    def get(self, request):
        api_key = os.environ.get('GEMINI_API_KEY', 'placeholder')
        persist_dir = os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db')
        
        # We shouldn't use QdrantIndexService directly here since it might have been refactored.
        # But for now, we'll proxy it via QdrantManager if needed, or leave it if it works.
        # Let's use the new Internal logic directly or QdrantManager
        from shared.services.qdrant_manager import QdrantManager
        client = QdrantManager.get_client(persist_dir)
        try:
            cohere_count = client.count(collection_name='construction_cohere_1024').count
            gemini_count = client.count(collection_name='construction_gemini_768').count
            nomic_count = client.count(collection_name='construction_nomic_768').count
            total = cohere_count + gemini_count + nomic_count
        except Exception:
            total = 0
            cohere_count = 0
            gemini_count = 0
            nomic_count = 0
            
        stats = {
            'total_vectors': total,
            'cohere_vectors': cohere_count,
            'gemini_vectors': gemini_count,
            'nomic_vectors': nomic_count,
            'persist_directory': persist_dir,
        }
        return Response(stats, status=status.HTTP_200_OK)

class ReindexDocumentView(APIView):
    def post(self, request, document_id):
        embed_and_index_task.delay(document_id=document_id, had_version_update=True)
        return Response({
            "status": "queued",
            "document_id": document_id,
            "message": "Re-indexing queued. Use GET /api/indexing/{document_id}/ to poll status."
        }, status=status.HTTP_202_ACCEPTED)

class HealthCheckView(APIView):
    def get(self, request):
        api_key = os.environ.get('GEMINI_API_KEY', 'placeholder')
        persist_dir = os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db')
        
        qdrant_connected = False
        total_vectors = 0
        error_msg = None
        try:
            from shared.services.qdrant_manager import QdrantManager
            client = QdrantManager.get_client(persist_dir)
            cohere_count = client.count(collection_name='construction_cohere_1024').count
            gemini_count = client.count(collection_name='construction_gemini_768').count
            nomic_count = client.count(collection_name='construction_nomic_768').count
            total_vectors = cohere_count + gemini_count + nomic_count
            qdrant_connected = True
        except Exception as e:
            error_msg = str(e)
            
        bm25_loaded = False
        try:
            bm25 = BM25IndexService.get_instance()
            bm25_loaded = bm25._index is not None
        except Exception:
            pass
            
        if qdrant_connected and bm25_loaded:
            return Response({
                "status": "ok",
                "qdrant_connected": True,
                "bm25_loaded": True,
                "total_vectors": total_vectors
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "status": "degraded",
                "qdrant_connected": qdrant_connected,
                "bm25_loaded": bm25_loaded,
                "total_vectors": total_vectors,
                "error": error_msg or "BM25 index not loaded properly"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class InternalQdrantView(APIView):
    """
    Internal API used exclusively by Celery workers to proxy Qdrant commands
    through the Django web server process, preventing RocksDB locks.
    """
    def post(self, request, action):
        from shared.services.qdrant_manager import QdrantManager
        from qdrant_client.http import models
        
        persist_dir = os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db')
        client = QdrantManager.get_client(persist_dir)
        
        # Ensure collections exist
        for collection_name, size in [('construction_cohere_1024', 1024), ('construction_gemini_768', 768), ('construction_nomic_768', 768)]:
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=size, distance=models.Distance.COSINE),
                )
        
        if action == "upsert":
            model_used = request.data.get('model_used', 'gemini')
            payloads = request.data.get('payloads', [])
            embeddings = request.data.get('embeddings', [])
            
            if not payloads or not embeddings:
                return Response({"count": 0})
                
            collection_name = 'construction_gemini_768'
            if model_used == "cohere":
                collection_name = 'construction_cohere_1024'
            elif model_used == "nomic":
                collection_name = 'construction_nomic_768'
            
            points = []
            for i, p in enumerate(payloads):
                points.append(
                    models.PointStruct(
                        id=p.get('chunk_id'),
                        vector=embeddings[i],
                        payload={
                            'page_content': p.get('preprocessed_text', ''),
                            'metadata': p
                        }
                    )
                )
                
            from filelock import FileLock
            lock_path = os.path.join(os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db'), 'write.lock')
            os.makedirs(os.path.dirname(lock_path), exist_ok=True)
            
            with FileLock(lock_path, timeout=60):
                client.upsert(
                    collection_name=collection_name,
                    points=points
                )
            return Response({"count": len(points)})
            
        elif action == "get_hashes":
            document_id = request.data.get('document_id')
            if not document_id:
                return Response({})
                
            filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
            
            existing = {}
            for collection_name in ['construction_cohere_1024', 'construction_gemini_768', 'construction_nomic_768']:
                try:
                    points, _ = client.scroll(
                        collection_name=collection_name,
                        scroll_filter=filter,
                        limit=10000,
                        with_payload=['metadata'],
                        with_vectors=True
                    )
                    for point in points:
                        meta = point.payload.get('metadata', {})
                        chunk_id = meta.get('chunk_id') or str(point.id)
                        hash_val = meta.get('content_hash')
                        if chunk_id and hash_val and point.vector:
                            existing[chunk_id] = {
                                'hash': hash_val,
                                'vector': point.vector,
                                'model_used': 'gemini' if 'gemini' in collection_name else ('cohere' if 'cohere' in collection_name else 'nomic')
                            }
                except Exception:
                    pass
            return Response(existing)
            
        elif action == "delete":
            document_id = request.data.get('document_id')
            if not document_id:
                return Response({"deleted": 0})
                
            filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
            
            total_deleted = 0
            for collection_name in ['construction_cohere_1024', 'construction_gemini_768', 'construction_nomic_768']:
                try:
                    count_result = client.count(
                        collection_name=collection_name,
                        count_filter=filter,
                    )
                    if count_result.count > 0:
                        from filelock import FileLock
                        lock_path = os.path.join(os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db'), 'write.lock')
                        with FileLock(lock_path, timeout=60):
                            client.delete(
                                collection_name=collection_name,
                                points_selector=filter,
                            )
                        total_deleted += count_result.count
                except Exception:
                    pass
            return Response({"deleted": total_deleted})
            
        elif action == "debug_payload":
            document_id = request.data.get('document_id')
            filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=str(document_id)),
                    )
                ]
            )
            for collection_name in ['construction_cohere_1024', 'construction_gemini_768', 'construction_nomic_768']:
                try:
                    points, _ = client.scroll(
                        collection_name=collection_name,
                        scroll_filter=filter,
                        limit=1,
                        with_payload=True
                    )
                    if points:
                        return Response({"payload": points[0].payload})
                except Exception:
                    pass
            return Response({"payload": None})
            
        return Response({"error": "Unknown action"}, status=400)
