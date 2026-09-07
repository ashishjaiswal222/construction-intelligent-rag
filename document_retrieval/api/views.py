import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from document_retrieval.api.serializers import QueryRequestSerializer
from document_retrieval.services.retrieval_pipeline import RetrievalPipeline
from document_retrieval.services.self_query_service import SelfQueryService
from document_retrieval.services.dense_search_service import DenseSearchService
from document_retrieval.services.sparse_search_service import SparseSearchService
from document_retrieval.services.fusion_service import FusionService
from document_retrieval.services.expansion_service import ExpansionService
from document_retrieval.services.reranking_service import RerankingService
from document_retrieval.services.crag_service import CRAGService
from document_retrieval.repositories.retrieval_repository import RetrievalRepository

# Module-level pipeline initialization to prevent re-loading BM25 on every request
# Triggering auto-reload
_pipeline = None

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = RetrievalPipeline(
            self_query_svc=SelfQueryService(os.environ.get('GROQ_API_KEY', '')),
            dense_svc=DenseSearchService(
                qdrant_path=os.environ.get('QDRANT_PATH', './construction_qdrant_db'),
                embedding_api_key=os.environ.get('GEMINI_API_KEY', ''),
            ),
            sparse_svc=SparseSearchService(
                bm25_index_path=os.environ.get('BM25_INDEX_PATH', './construction_bm25_index.pkl'),
            ),
            fusion_svc=FusionService(),
            expansion_svc=ExpansionService(RetrievalRepository()),
            reranking_svc=RerankingService(
                cohere_api_key=os.environ.get('COHERE_API_KEY', '')
            ),
            crag_svc=CRAGService(os.environ.get('GROQ_API_KEY', '')),
        )
    return _pipeline

class RetrievalQueryView(APIView):
    def post(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        pipeline = get_pipeline()
        result = pipeline.retrieve(
            user_query=serializer.validated_data['query'],
            project_id=serializer.validated_data.get('project_id')
        )
        
        # Only return the chunks and necessary metadata for production
        return Response({
            'chunks': [c.model_dump() for c in result.chunks],
            'needs_fallback': result.needs_fallback
        }, status=status.HTTP_200_OK)

class RetrievalQueryDebugView(APIView):
    def post(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        pipeline = get_pipeline()
        result = pipeline.retrieve(
            user_query=serializer.validated_data['query'],
            project_id=serializer.validated_data.get('project_id')
        )
        
        # Return full RetrievalResult dump for debugging
        return Response(result.model_dump(), status=status.HTTP_200_OK)

class RetrievalHealthView(APIView):
    def get(self, request):
        pipeline = get_pipeline()
        qdrant_reachable = True
        try:
            pipeline.dense_svc.client.get_collections()
        except:
            qdrant_reachable = False
            
        bm25_loaded = pipeline.sparse_svc._index is not None
        chunk_count = len(pipeline.sparse_svc._chunks)
        
        status_str = 'ok' if (qdrant_reachable and bm25_loaded) else 'degraded'
        
        return Response({
            'status': status_str,
            'qdrant': qdrant_reachable,
            'bm25_loaded': bm25_loaded,
            'bm25_chunk_count': chunk_count,
        }, status=status.HTTP_200_OK)
