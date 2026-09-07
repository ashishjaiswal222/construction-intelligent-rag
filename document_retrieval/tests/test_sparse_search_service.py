import pytest
from unittest.mock import patch, MagicMock
from document_retrieval.services.sparse_search_service import SparseSearchService
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.schemas.retrieval_result import RetrievedChunk

class TestSparseSearchService:
    @patch('os.path.exists')
    @patch('builtins.open')
    @patch('pickle.load')
    def test_loads_corpus_and_rebuilds_index(self, mock_load, mock_open, mock_exists):
        mock_exists.return_value = True
        mock_load.return_value = {
            'doc_ids': ['id1', 'id2'],
            'corpus': [['word1'], ['word2']]
        }
        
        svc = SparseSearchService("fake_path")
        
        assert svc._doc_ids == ['id1', 'id2']
        assert svc._index is not None
        assert svc._index.corpus_size == 2

    @patch('document_retrieval.repositories.retrieval_repository.RetrievalRepository')
    def test_search_hydrates_via_repository(self, mock_repo_class):
        svc = SparseSearchService("fake_path")
        # Mock the internal state as if it loaded
        svc._doc_ids = ['id1', 'id2', 'id3']
        
        mock_index = MagicMock()
        mock_index.get_scores.return_value = [0.9, 0.0, 0.5] # id1 and id3 are > 0
        svc._index = mock_index
        
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        
        chunk1 = RetrievedChunk(
            chunk_id="id1", content="", doc_type="", document_id="", project_id="", filename="", 
            revision="", is_current=True, chunk_type="text", score=0.0
        )
        chunk3 = RetrievedChunk(
            chunk_id="id3", content="", doc_type="", document_id="", project_id="", filename="", 
            revision="", is_current=True, chunk_type="text", score=0.0
        )
        mock_repo.get_chunks_by_ids.return_value = [chunk1, chunk3]
        
        filters = QueryFilters(semantic_query="test", sub_queries=[])
        results = svc.search("word1", filters, top_k=2)
        
        # Verify repo was called with the candidates
        mock_repo.get_chunks_by_ids.assert_called_once()
        candidate_ids = mock_repo.get_chunks_by_ids.call_args[0][0]
        assert set(candidate_ids) == {'id1', 'id3'}
        
        # Verify scores were applied and sorted correctly
        assert len(results) == 2
        assert results[0].chunk_id == "id1"
        assert results[0].score == 0.9
        assert results[1].chunk_id == "id3"
        assert results[1].score == 0.5
