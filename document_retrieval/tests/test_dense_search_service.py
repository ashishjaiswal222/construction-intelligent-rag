import pytest
from unittest.mock import patch, MagicMock
from document_retrieval.services.dense_search_service import DenseSearchService
from document_retrieval.schemas.query_filters import QueryFilters

class TestDenseSearchService:
    @patch('os.makedirs')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    @patch('qdrant_client.QdrantClient')
    def test_multi_query_search_uses_batch_embedding(self, mock_qdrant, mock_embed, mock_makedirs):
        # Setup mocks
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        
        # Simulate embed_documents returning 2 vectors
        mock_embed_instance.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
        
        mock_qdrant_instance = MagicMock()
        mock_qdrant.return_value = mock_qdrant_instance
        
        # Create fake search results
        mock_result1 = MagicMock()
        mock_result1.id = "id1"
        mock_result1.payload = {"content": "test1"}
        mock_result1.score = 0.9
        
        mock_result2 = MagicMock()
        mock_result2.id = "id2"
        mock_result2.payload = {"content": "test2"}
        mock_result2.score = 0.8
        
        # client.search called 2 times in the loop, each returns 1 result
        mock_qdrant_instance.search.side_effect = [[mock_result1], [mock_result2]]
        
        # Init
        svc = DenseSearchService("fake_path", "fake_key")
        
        # Exec
        filters = QueryFilters(semantic_query="test", sub_queries=[])
        results = svc.multi_query_search(["query1", "query2"], filters)
        
        # Assertions
        mock_makedirs.assert_called_once_with("fake_path", exist_ok=True)
        mock_embed_instance.embed_documents.assert_called_once_with(["query1", "query2"])
        assert mock_qdrant_instance.search.call_count == 2
        assert len(results) == 2
        assert results[0].chunk_id == "id1"
        assert results[1].chunk_id == "id2"
