import pytest
from unittest.mock import patch, MagicMock
from document_retrieval.services.reranking_service import RerankingService
from document_retrieval.schemas.retrieval_result import RetrievedChunk

def make_chunk(chunk_id: str, content: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        doc_type="drawing",
        document_id="doc1",
        project_id="proj1",
        filename="draw.pdf",
        revision="A",
        is_current=True,
        chunk_type="generic",
        score=0.0
    )

class TestRerankingService:
    @patch('cohere.Client')
    def test_returns_top_k_on_success(self, mock_cohere_client):
        mock_client = MagicMock()
        mock_cohere_client.return_value = mock_client
        
        # Mocking Cohere response
        mock_response = MagicMock()
        mock_res_1 = MagicMock()
        mock_res_1.index = 1
        mock_res_2 = MagicMock()
        mock_res_2.index = 0
        mock_response.results = [mock_res_1, mock_res_2]
        mock_client.rerank.return_value = mock_response
        
        service = RerankingService("dummy_key")
        chunks = [make_chunk("c1", "bad"), make_chunk("c2", "good"), make_chunk("c3", "worst")]
        
        result = service.rerank("query", chunks, top_k=2)
        
        assert len(result) == 2
        assert result[0].chunk_id == "c2"
        assert result[1].chunk_id == "c1"
        
    @patch('cohere.Client')
    def test_falls_back_to_score_order_on_cohere_exception(self, mock_cohere_client):
        mock_client = MagicMock()
        mock_cohere_client.return_value = mock_client
        mock_client.rerank.side_effect = Exception("Cohere 429")
        
        service = RerankingService("dummy_key")
        chunks = [make_chunk("c1", "test1"), make_chunk("c2", "test2")]
        
        result = service.rerank("query", chunks, top_k=1)
        
        # Falls back to top-k of original order
        assert len(result) == 1
        assert result[0].chunk_id == "c1"

    @patch('cohere.Client')
    def test_circuit_opens_after_three_failures(self, mock_cohere_client):
        mock_client = MagicMock()
        mock_cohere_client.return_value = mock_client
        mock_client.rerank.side_effect = Exception("Cohere 429")
        
        service = RerankingService("dummy_key")
        chunks = [make_chunk("c1", "test")]
        
        assert service._circuit_open is False
        service.rerank("query", chunks)
        service.rerank("query", chunks)
        service.rerank("query", chunks)
        
        assert service._circuit_open is True

    @patch('cohere.Client')
    def test_circuit_open_skips_api_call(self, mock_cohere_client):
        mock_client = MagicMock()
        mock_cohere_client.return_value = mock_client
        
        service = RerankingService("dummy_key")
        service._circuit_open = True
        
        chunks = [make_chunk("c1", "test")]
        result = service.rerank("query", chunks)
        
        mock_client.rerank.assert_not_called()
        assert len(result) == 1
