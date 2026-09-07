import time
from typing import Optional
from rag_generation.schemas.generation_request import GenerationRequest
from rag_generation.schemas.generation_response import GenerationResponse
from rag_generation.services.context_builder import ContextBuilder
from rag_generation.services.generator_service import GeneratorService
from rag_generation.services.hallucination_guard import HallucinationGuard
from rag_generation.repositories.generation_repository import GenerationRepository

class GenerationPipeline:

    def __init__(
        self,
        context_builder: ContextBuilder,
        generator: GeneratorService,
        guard: HallucinationGuard,
        repository: GenerationRepository,
    ):
        from mem0 import MemoryClient
        self.context_builder = context_builder
        self.generator = generator
        self.guard = guard
        self.repository = repository
        self.memory_client = MemoryClient(api_key="m0-Mr8IKVqUL5KpR9ff0XmY6px1zyTGjTS0NQIb7j5F")

    def generate(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """
        3-stage pipeline:
        """
        start = time.time()
        
        try:
            # Mem0 Long-term Memory Retrieval
            mem0_context = ""
            try:
                # We use a static user_id for simplicity or pull from request if available.
                # Since GenerationRequest doesn't have user_id, we will use a generic 'user' 
                # or project_id to namespace memory if needed, but let's just use a hardcoded 'admin_user'
                mem0_res = self.memory_client.search(request.user_query, filters={"user_id": "admin_user"})
                if mem0_res:
                    mem_facts = [m.get("memory", "") for m in mem0_res if "memory" in m]
                    if mem_facts:
                        mem0_context = "Mem0 Context: " + "; ".join(mem_facts) + "\n\n"
            except Exception as e:
                print("Mem0 search error:", e)

            # Stage 1 — Context Building
            context_string, citations = self.context_builder.build(
                request.retrieval_result.chunks,
                request.user_query,
            )
            
            # Prepend mem0_context to context_string
            full_context_string = mem0_context + context_string

            if not citations and not mem0_context:
                return self._build_failure_response(request, "No relevant documents found.")
                
            # Stage 2 — Generation
            answer = self.generator.generate(
                request.user_query,
                full_context_string,
                request.retrieval_result.needs_fallback,
            )
            
            if answer == GeneratorService.FAILURE_MESSAGE:
                return self._build_failure_response(request, answer)

            # Mem0 Store Background
            try:
                import threading
                def store_mem():
                    try:
                        self.memory_client.add([
                            {"role": "user", "content": request.user_query},
                            {"role": "assistant", "content": answer}
                        ], user_id="admin_user")
                    except Exception:
                        pass
                threading.Thread(target=store_mem).start()
            except Exception:
                pass

            # Stage 3 — Hallucination check
            is_grounded, warning = self.guard.check(
                request.user_query,
                answer,
                full_context_string,
            )

            # Calculate confidence
            chunks_provided = len(request.retrieval_result.chunks)
            chunks_used = len(citations)
            used_chunk_ids = [c.chunk_id for c in citations]
            
            # Find scores of used chunks
            used_scores = [
                chunk.score for chunk in request.retrieval_result.chunks
                if chunk.chunk_id in used_chunk_ids
            ]
            avg_score = sum(used_scores) / len(used_scores) if used_scores else 0.0
            
            confidence = (chunks_used / max(chunks_provided, 1)) * avg_score
            if request.retrieval_result.needs_fallback:
                confidence = min(confidence, 0.6)

            # Set warning_message
            warning_message = None
            if not is_grounded:
                warning_message = warning
            elif request.retrieval_result.needs_fallback:
                warning_message = "Answer may be incomplete — source documents for this specific query were not found."

            generation_ms = int((time.time() - start) * 1000)

            # Save to audit log
            log = self.repository.save_log(
                project_id=request.project_id or '',
                user_query=request.user_query,
                answer=answer,
                confidence=confidence,
                answer_grounded=is_grounded,
                needs_fallback=request.retrieval_result.needs_fallback,
                chunks_used=chunks_used,
                chunk_ids_used=used_chunk_ids,
                filter_used=request.retrieval_result.filter_used,
                stages_completed=request.retrieval_result.stages_completed,
                retrieval_ms=request.retrieval_result.processing_ms,
                generation_ms=generation_ms,
                model_used=self.generator.MODEL,
                warning_message=warning_message or '',
            )

            return GenerationResponse(
                log_id=str(log.id) if log else None,
                answer=answer,
                citations=citations,
                confidence=confidence,
                needs_fallback=request.retrieval_result.needs_fallback,
                answer_grounded=is_grounded,
                warning_message=warning_message,
                retrieval_stages=request.retrieval_result.stages_completed,
                processing_ms=generation_ms
            )
            
        except Exception as e:
            # NEVER raises
            generation_ms = int((time.time() - start) * 1000)
            self.repository.save_log(
                project_id=request.project_id or '',
                user_query=request.user_query,
                answer=GeneratorService.FAILURE_MESSAGE,
                confidence=0.0,
                answer_grounded=False,
                needs_fallback=request.retrieval_result.needs_fallback,
                chunks_used=0,
                chunk_ids_used=[],
                filter_used=request.retrieval_result.filter_used,
                stages_completed=request.retrieval_result.stages_completed,
                retrieval_ms=request.retrieval_result.processing_ms,
                generation_ms=generation_ms,
                model_used=self.generator.MODEL,
                warning_message=str(e),
            )
            return self._build_failure_response(request, GeneratorService.FAILURE_MESSAGE)

    def _build_failure_response(self, request: GenerationRequest, msg: str) -> GenerationResponse:
        return GenerationResponse(
            answer=msg,
            citations=[],
            confidence=0.0,
            needs_fallback=request.retrieval_result.needs_fallback,
            answer_grounded=False,
            warning_message=None,
            retrieval_stages=request.retrieval_result.stages_completed,
            processing_ms=0
        )
