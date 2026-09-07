import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from document_retrieval.services.retrieval_pipeline import RetrievalPipeline
from document_retrieval.services.self_query_service import SelfQueryService
from document_retrieval.services.dense_search_service import DenseSearchService
from document_retrieval.services.sparse_search_service import SparseSearchService
from document_retrieval.services.fusion_service import FusionService
from document_retrieval.services.expansion_service import ExpansionService
from document_retrieval.services.reranking_service import RerankingService
from document_retrieval.services.crag_service import CRAGService
from document_retrieval.repositories.retrieval_repository import RetrievalRepository

from rag_generation.services.generation_pipeline import GenerationPipeline
from rag_generation.services.context_builder import ContextBuilder
from rag_generation.services.generator_service import GeneratorService
from rag_generation.services.hallucination_guard import HallucinationGuard
from rag_generation.repositories.generation_repository import GenerationRepository
from rag_generation.schemas.generation_request import GenerationRequest
from rag_generation.api.serializers import GenerationRequestSerializer

_retrieval_pipeline = None
_generation_pipeline = None

def get_retrieval_pipeline():
    global _retrieval_pipeline
    if _retrieval_pipeline is None:
        _retrieval_pipeline = RetrievalPipeline(
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
            reranking_svc=RerankingService(os.environ.get('COHERE_API_KEY', '')),
            crag_svc=CRAGService(os.environ.get('GROQ_API_KEY', '')),
        )
    return _retrieval_pipeline

def get_generation_pipeline():
    global _generation_pipeline
    if _generation_pipeline is None:
        _generation_pipeline = GenerationPipeline(
            context_builder=ContextBuilder(),
            generator=GeneratorService(os.environ.get('GROQ_API_KEY', '')),
            guard=HallucinationGuard(os.environ.get('GROQ_API_KEY', '')),
            repository=GenerationRepository(),
        )
    return _generation_pipeline

class GenerateView(APIView):
    def post(self, request):
        serializer = GenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data['query']
        project_id = serializer.validated_data.get('project_id')
        chat_history = serializer.validated_data.get('chat_history', [])

        if project_id and hasattr(request, 'user') and request.user.is_authenticated:
            try:
                if not request.user.has_project_access(project_id):
                    return Response({"error": "Access denied for this project"}, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({"error": f"Invalid project ID: {e}"}, status=status.HTTP_400_BAD_REQUEST)
        elif not project_id:
            return Response({"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Smart Conversational Router
        generation_pipeline = get_generation_pipeline()
        intent = generation_pipeline.generator.classify_intent(query)
        
        if intent == "CHAT":
            # Retrieve Mem0 context
            mem0_context = ""
            try:
                mem0_res = generation_pipeline.memory_client.search(query, filters={"user_id": "admin_user"})
                if mem0_res:
                    mem_facts = [m.get("memory", "") for m in mem0_res if "memory" in m]
                    if mem_facts:
                        mem0_context = "; ".join(mem_facts)
            except Exception as e:
                print("Mem0 search error:", e)

            # Generate conversational response
            chat_answer = generation_pipeline.generator.generate_conversational_response(query, chat_history, mem0_context)

            # Store in Mem0
            try:
                import threading
                def store_mem_chat():
                    try:
                        generation_pipeline.memory_client.add([
                            {"role": "user", "content": query},
                            {"role": "assistant", "content": chat_answer}
                        ], user_id="admin_user")
                    except Exception:
                        pass
                threading.Thread(target=store_mem_chat).start()
            except Exception:
                pass

            from rag_generation.schemas.generation_response import GenerationResponse
            return Response(GenerationResponse(
                answer=chat_answer,
                citations=[],
                confidence=1.0,
                needs_fallback=False,
                answer_grounded=True,
                warning_message=None,
                retrieval_stages=["chit_chat"],
                processing_ms=10
            ).model_dump())
        
        # 2. Rewrite query for context
        rewritten_query = query
        if chat_history:
            rewritten_query = generation_pipeline.generator.rewrite_query(query, chat_history)

        # 3. Retrieve chunks
        retrieval_pipeline = get_retrieval_pipeline()
        retrieval_result = retrieval_pipeline.retrieve(rewritten_query, project_id)

        # 4. Build GenerationRequest
        gen_request = GenerationRequest(
            user_query=rewritten_query,
            project_id=project_id,
            retrieval_result=retrieval_result,
            chat_history=chat_history,
        )

        # 3. Generate Answer
        generation_pipeline = get_generation_pipeline()
        response = generation_pipeline.generate(gen_request)

        # 4. Return
        return Response(response.model_dump())

class GenerateDebugView(APIView):
    def post(self, request):
        serializer = GenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        query = serializer.validated_data['query']
        project_id = serializer.validated_data.get('project_id')

        retrieval_pipeline = get_retrieval_pipeline()
        retrieval_result = retrieval_pipeline.retrieve(query, project_id)
        
        gen_request = GenerationRequest(
            user_query=query,
            project_id=project_id,
            retrieval_result=retrieval_result,
        )

        generation_pipeline = get_generation_pipeline()
        response = generation_pipeline.generate(gen_request)
        
        data = response.model_dump()
        data['debug'] = {
            'retrieval_result': retrieval_result.model_dump(),
        }

        return Response(data)

class GenerateAuditView(APIView):
    def get(self, request):
        project_id = request.query_params.get('project_id')
        if not project_id:
            return Response({"error": "project_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                if not request.user.has_project_access(project_id):
                    return Response({"error": "Access denied for this project"}, status=status.HTTP_403_FORBIDDEN)
            except Exception as e:
                return Response({"error": f"Invalid project ID: {e}"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            limit = int(request.query_params.get('limit', 20))
        except ValueError:
            limit = 20

        repo = GenerationRepository()
        logs = repo.get_recent_logs(project_id, limit)
        
        data = []
        for log in logs:
            data.append({
                "user_query": log.user_query,
                "generated_answer": log.generated_answer,
                "confidence": log.confidence,
                "answer_grounded": log.answer_grounded,
                "chunks_used": log.chunks_used,
                "created_at": log.created_at.isoformat()
            })
            
        return Response(data)

class GenerateHealthView(APIView):
    def get(self, request):
        from rag_generation.models.generation_log import GenerationLog
        
        try:
            total_logs = GenerationLog.objects.count()
        except Exception:
            total_logs = 0

        guard_circuit = False
        if _generation_pipeline and _generation_pipeline.guard:
            guard_circuit = _generation_pipeline.guard._circuit_open

        return Response({
            "status": "ok",
            "groq_configured": bool(os.environ.get('GROQ_API_KEY')),
            "guard_circuit_open": guard_circuit,
            "total_logs": total_logs
        })

class GenerateFeedbackView(APIView):
    def post(self, request, pk):
        from rag_generation.models.generation_log import GenerationLog
        
        try:
            log = GenerationLog.objects.get(id=pk)
        except GenerationLog.DoesNotExist:
            return Response({"error": "Log not found"}, status=status.HTTP_404_NOT_FOUND)
            
        thumbs_up = request.data.get('thumbs_up')
        if thumbs_up is None:
            return Response({"error": "thumbs_up boolean is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        log.thumbs_up = bool(thumbs_up)
        log.save(update_fields=['thumbs_up'])
        
        return Response({"status": "success"})
