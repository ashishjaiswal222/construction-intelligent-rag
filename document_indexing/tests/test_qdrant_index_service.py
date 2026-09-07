import pytest
from unittest.mock import patch, MagicMock
from document_indexing.services.qdrant_index_service import QdrantIndexService
from document_indexing.schemas.chunk_payload import ChunkPayload

class TestQdrantIndexService:
    @patch('langchain_qdrant.QdrantVectorStore')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    @patch('qdrant_client.QdrantClient')
    def test_upsert_chunks_converts_none_to_empty_string(self, mock_client_cls, mock_embeddings, mock_store_cls):
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store
        
        service = QdrantIndexService('dir', 'fake_key')
        
        payload = ChunkPayload(
            chunk_id='1', document_id='d1', collection_name='c', raw_text='r',
            project_id=None, revision=None
        )
        
        service.upsert_chunks([payload], [[0.1]*768])
        
        called_metadatas = mock_store.add_texts.call_args[1]['metadatas']
        assert called_metadatas[0]['project_id'] == ''
        assert called_metadatas[0]['revision'] == ''

    @patch('langchain_qdrant.QdrantVectorStore')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    @patch('qdrant_client.QdrantClient')
    def test_upsert_is_idempotent_on_retry(self, mock_client_cls, mock_embeddings, mock_store_cls):
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store
        
        service = QdrantIndexService('dir', 'fake_key')
        payload = ChunkPayload(chunk_id='chunk_123', document_id='d1', collection_name='c', raw_text='r')
        
        service.upsert_chunks([payload], [[0.1]*768])
        
        # Check that chunk_id was used as id
        called_ids = mock_store.add_texts.call_args[1]['ids']
        assert called_ids == ['chunk_123']

    @patch('langchain_qdrant.QdrantVectorStore')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    @patch('qdrant_client.QdrantClient')
    def test_delete_chunks_removes_all_for_document(self, mock_client_cls, mock_embeddings, mock_store_cls):
        mock_client = MagicMock()
        # Mock count result
        mock_count_result = MagicMock()
        mock_count_result.count = 2
        mock_client.count.return_value = mock_count_result
        
        mock_client_cls.return_value = mock_client
        
        service = QdrantIndexService('dir', 'fake_key')
        deleted = service.delete_chunks_for_document('d1')
        
        # It should count 2 times (gemini, nomic) and delete 2 times
        assert deleted == 4
        assert mock_client.count.call_count == 2
        assert mock_client.delete.call_count == 2

    @patch('langchain_qdrant.QdrantVectorStore')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    @patch('qdrant_client.QdrantClient')
    def test_metadata_dict_has_required_keys(self, mock_client_cls, mock_embeddings, mock_store_cls):
        mock_store = MagicMock()
        mock_store_cls.return_value = mock_store
        
        service = QdrantIndexService('dir', 'fake_key')
        payload = ChunkPayload(chunk_id='chunk_1', document_id='doc_1', collection_name='c', raw_text='r')
        
        service.upsert_chunks([payload], [[0.1]*768])
        
        meta = mock_store.add_texts.call_args[1]['metadatas'][0]
        assert 'is_current' in meta
        assert 'project_id' in meta
        assert 'chunk_id' in meta
        assert 'document_id' in meta
