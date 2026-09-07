import pytest
from unittest.mock import MagicMock
from document_retrieval.services.retrieval_pipeline import RetrievalPipeline
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.schemas.retrieval_result import RetrievedChunk

def make_chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content="dummy content",
        doc_type="drawing",
        document_id="doc1",
        project_id="proj1",
        filename="draw.pdf",
        revision="A",
        is_current=True,
        chunk_type="generic",
        score=0.0
    )

class TestRetrievalPipeline:
    def setup_method(self):
        self.self_query_svc = MagicMock()
        self.dense_svc = MagicMock()
        self.sparse_svc = MagicMock()
        self.fusion_svc = MagicMock()
        self.expansion_svc = MagicMock()
        self.reranking_svc = MagicMock()
        self.crag_svc = MagicMock()
        
        self.pipeline = RetrievalPipeline(
            self_query_svc=self.self_query_svc,
            dense_svc=self.dense_svc,
            sparse_svc=self.sparse_svc,
            fusion_svc=self.fusion_svc,
            expansion_svc=self.expansion_svc,
            reranking_svc=self.reranking_svc,
            crag_svc=self.crag_svc
        )

    def test_full_pipeline_returns_retrieval_result(self):
        self.self_query_svc.extract_filters.return_value = QueryFilters(
            semantic_query="test", sub_queries=["test1"]
        )
        self.dense_svc.multi_query_search.return_value = [make_chunk("d1")]
        self.sparse_svc.search.return_value = [make_chunk("s1")]
        fused = [make_chunk("d1"), make_chunk("s1")]
        self.fusion_svc.rrf_fuse.return_value = fused
        self.expansion_svc.expand.return_value = fused
        self.reranking_svc.rerank.return_value = fused
        self.crag_svc.grade_and_filter.return_value = (fused, False)
        
        result = self.pipeline.retrieve("test query")
        
        assert len(result.chunks) == 2
        assert result.needs_fallback is False
        assert result.final_count == 2
        assert 'self_query' in result.stages_completed
        assert 'crag_grading' in result.stages_completed

    def test_fallback_triggered_when_crag_rejects_all(self):
        self.self_query_svc.extract_filters.return_value = QueryFilters(
            semantic_query="test", sub_queries=["test1"], doc_type="drawing", is_current=True
        )
        self.dense_svc.multi_query_search.return_value = [make_chunk("d1")]
        self.sparse_svc.search.return_value = []
        self.fusion_svc.rrf_fuse.return_value = [make_chunk("d1")]
        self.expansion_svc.expand.return_value = [make_chunk("d1")]
        
        # When reranking loose chunks, return them
        self.reranking_svc.rerank.side_effect = [
            [make_chunk("d1")], # First normal rerank
            [make_chunk("loose_d1")] # Fallback rerank
        ]

        # CRAG rejects everything
        self.crag_svc.grade_and_filter.return_value = ([], True)
        
        # Fallback loose search finds something
        self.dense_svc.search.return_value = [make_chunk("loose_d1")]
        
        result = self.pipeline.retrieve("test query")
        
        assert result.needs_fallback is True
        assert len(result.chunks) == 1
        assert result.chunks[0].chunk_id == "loose_d1"
        assert 'fallback_loose_search' in result.stages_completed
        
        # Verify the loose search loosened the right filters
        loose_filters_used = self.dense_svc.search.call_args[0][1]
        assert loose_filters_used.doc_type is None
        assert loose_filters_used.is_current is True # Should keep is_current

    def test_project_id_injected_into_filters(self):
        self.self_query_svc.extract_filters.return_value = QueryFilters(
            semantic_query="test", sub_queries=[]
        )
        self.crag_svc.grade_and_filter.return_value = ([], False)
        
        result = self.pipeline.retrieve("test query", project_id="PROJ-INJECT")
        
        assert result.filter_used['project_id'] == "PROJ-INJECT"

    def test_is_current_defaults_to_true(self):
        self.self_query_svc.extract_filters.return_value = QueryFilters(
            semantic_query="test", sub_queries=[]
        )
        self.crag_svc.grade_and_filter.return_value = ([], False)
        
        result = self.pipeline.retrieve("test query")
        
        assert result.filter_used['is_current'] is True
