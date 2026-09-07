import time
from typing import Optional
from document_retrieval.schemas.retrieval_result import RetrievalResult
from document_retrieval.services.self_query_service import SelfQueryService
from document_retrieval.services.dense_search_service import DenseSearchService
from document_retrieval.services.sparse_search_service import SparseSearchService
from document_retrieval.services.fusion_service import FusionService
from document_retrieval.services.expansion_service import ExpansionService
from document_retrieval.services.reranking_service import RerankingService
from document_retrieval.services.crag_service import CRAGService

class RetrievalPipeline:
    def __init__(
        self,
        self_query_svc: SelfQueryService,
        dense_svc: DenseSearchService,
        sparse_svc: SparseSearchService,
        fusion_svc: FusionService,
        expansion_svc: ExpansionService,
        reranking_svc: RerankingService,
        crag_svc: CRAGService,
    ):
        self.self_query_svc = self_query_svc
        self.dense_svc = dense_svc
        self.sparse_svc = sparse_svc
        self.fusion_svc = fusion_svc
        self.expansion_svc = expansion_svc
        self.reranking_svc = reranking_svc
        self.crag_svc = crag_svc

    def retrieve(
        self,
        user_query: str,
        project_id: Optional[str] = None,
    ) -> RetrievalResult:
        start = time.time()
        stages: list[str] = []

        # STAGE 1 — Self-query filter extraction
        filters = self.self_query_svc.extract_filters(user_query)
        if project_id:
            filters = filters.model_copy(
                update={'project_id': project_id}
            )
        if filters.is_current is None:
            filters = filters.model_copy(
                update={'is_current': True}
            )
        stages.append('self_query')

        # STAGE 2 — Hybrid retrieval
        # Deduplicate identical strings to save API tokens
        all_queries = list(dict.fromkeys([
            user_query,
            filters.semantic_query,
        ] + filters.sub_queries))

        dense_results = self.dense_svc.multi_query_search(
            all_queries, filters, top_k_per_query=15
        )
        sparse_results = self.sparse_svc.search(
            user_query, filters, top_k=30
        )
        stages.append('hybrid_retrieval')

        # STAGE 3 — RRF fusion
        fused = self.fusion_svc.rrf_fuse(
            dense_results, sparse_results, top_k=40
        )
        stages.append('rrf_fusion')

        # STAGE 4 — Parent-child expansion
        expanded = self.expansion_svc.expand(fused, max_parents=5)
        stages.append('parent_child_expansion')

        # STAGE 5 — Cohere reranking
        reranked = self.reranking_svc.rerank(
            user_query, expanded, top_k=8
        )
        stages.append('cohere_reranking')

        # STAGE 6 — CRAG relevance check
        relevant, needs_fallback = self.crag_svc.grade_and_filter(
            user_query, reranked
        )
        stages.append('crag_grading')

        # FALLBACK: if CRAG rejects all, retry with loosened filters
        if needs_fallback:
            loose_filters = filters.model_copy(
                update={
                    'doc_type': None,
                    'discipline': None,
                    'floor_level': None,
                }
            )
            dense_loose = self.dense_svc.search(
                user_query, loose_filters, top_k=10
            )
            if dense_loose:
                # Pass the fallback chunks through Reranking to ensure quality
                reranked_loose = self.reranking_svc.rerank(
                    user_query, dense_loose, top_k=5
                )
                relevant = reranked_loose
                # We still leave needs_fallback=True so the generation layer 
                # knows this is a low-confidence hallucination risk.
                stages.append('fallback_loose_search')

        return RetrievalResult(
            chunks=relevant,
            needs_fallback=needs_fallback,
            filter_used=filters.model_dump(),
            candidates_found=len(fused),
            final_count=len(relevant),
            stages_completed=stages,
            processing_ms=int((time.time() - start) * 1000),
        )
