import pytest
from document_retrieval.services.fusion_service import FusionService
from document_retrieval.schemas.retrieval_result import RetrievedChunk

def make_chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content="dummy",
        doc_type="drawing",
        document_id="doc1",
        project_id="proj1",
        filename="draw.pdf",
        revision="A",
        is_current=True,
        chunk_type="generic",
        score=0.0
    )

class TestFusionService:
    def test_rrf_boosts_chunk_appearing_in_both_lists(self):
        service = FusionService()
        dense = [make_chunk("chunk1"), make_chunk("chunk2"), make_chunk("chunk3")]
        sparse = [make_chunk("chunk4"), make_chunk("chunk1"), make_chunk("chunk5")]
        
        result = service.rrf_fuse(dense, sparse)
        
        assert len(result) == 5
        assert result[0].chunk_id == "chunk1"  # Should be highest because it's in both
        
    def test_deduplicates_by_chunk_id(self):
        service = FusionService()
        dense = [make_chunk("chunk1")]
        sparse = [make_chunk("chunk1")]
        
        result = service.rrf_fuse(dense, sparse)
        
        assert len(result) == 1
        assert result[0].chunk_id == "chunk1"
        
    def test_empty_dense_returns_sparse_only(self):
        service = FusionService()
        dense = []
        sparse = [make_chunk("chunk1"), make_chunk("chunk2")]
        
        result = service.rrf_fuse(dense, sparse)
        
        assert len(result) == 2
        assert {r.chunk_id for r in result} == {"chunk1", "chunk2"}
        
    def test_empty_both_returns_empty(self):
        service = FusionService()
        result = service.rrf_fuse([], [])
        assert len(result) == 0
