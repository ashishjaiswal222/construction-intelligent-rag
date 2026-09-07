import pytest
from unittest.mock import patch, MagicMock
from document_indexing.services.embedding_service import EmbeddingService
from document_indexing.schemas.chunk_payload import ChunkPayload

class TestEmbeddingService:
    @patch('django.core.cache.cache.get', return_value=False)
    @patch('langchain_community.embeddings.OllamaEmbeddings')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_embed_batch_returns_gemini_on_success(self, mock_gemini_cls, mock_ollama_cls, mock_cache_get):
        mock_gemini = MagicMock()
        mock_gemini.embed_documents.return_value = [[0.1] * 768] * 2
        mock_gemini_cls.return_value = mock_gemini
        
        service = EmbeddingService(api_key='fake')
        vectors, waits, model = service.embed_batch(['text1', 'text2'], 'doc_1')
        
        assert len(vectors) == 2
        assert waits == 0
        assert model == 'gemini'

    @patch('time.sleep')
    @patch('django.core.cache.cache.get', return_value=False)
    @patch('langchain_community.embeddings.OllamaEmbeddings')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_embed_batch_retries_on_429(self, mock_gemini_cls, mock_ollama_cls, mock_cache_get, mock_sleep):
        mock_gemini = MagicMock()
        mock_gemini.embed_documents.side_effect = [Exception('429 Too Many Requests'), [[0.1]*768]]
        mock_gemini_cls.return_value = mock_gemini
        
        service = EmbeddingService(api_key='fake')
        vectors, waits, model = service.embed_batch(['text1'], 'doc_1')
        
        assert len(vectors) == 1
        assert waits == 1
        assert model == 'gemini'
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(60)

    @patch('django.core.cache.cache.set')
    @patch('django.core.cache.cache.get')
    @patch('langchain_community.embeddings.OllamaEmbeddings')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_falls_back_to_ollama_on_hard_failure(self, mock_gemini_cls, mock_ollama_cls, mock_cache_get, mock_cache_set):
        mock_gemini = MagicMock()
        mock_gemini.embed_documents.side_effect = Exception('503 Service Unavailable')
        mock_gemini_cls.return_value = mock_gemini
        
        mock_ollama = MagicMock()
        mock_ollama.embed_documents.return_value = [[0.9]*768]
        mock_ollama_cls.return_value = mock_ollama
        
        # Mock cache to return circuit closed, then consecutive failures = 0
        mock_cache_get.side_effect = [False, 0]
        
        service = EmbeddingService(api_key='fake')
        vectors, waits, model = service.embed_batch(['text1'], 'doc_1')
        
        assert len(vectors) == 1
        assert vectors[0] == [0.9]*768
        assert model == 'nomic'
        assert waits == 0

    @patch('langchain_community.embeddings.OllamaEmbeddings')
    @patch('langchain_google_genai.GoogleGenerativeAIEmbeddings')
    def test_embed_chunks_batched_respects_batch_size_100(self, mock_gemini_cls, mock_ollama_cls):
        mock_gemini = MagicMock()
        mock_gemini.embed_documents.side_effect = lambda texts: [[0.1]*768 for _ in texts]
        mock_gemini_cls.return_value = mock_gemini
        
        service = EmbeddingService(api_key='fake')
        
        payloads = [
            ChunkPayload(
                chunk_id=str(i), document_id='doc_1', collection_name='c', raw_text='r', preprocessed_text='p'
            ) for i in range(250)
        ]
        
        with patch.object(service, 'embed_batch', wraps=service.embed_batch) as spy_batch:
            vectors, waits, model = service.embed_chunks_batched(payloads, 'doc_1', batch_size=100)
            assert spy_batch.call_count == 3
            assert len(spy_batch.call_args_list[0][0][0]) == 100
            assert len(spy_batch.call_args_list[1][0][0]) == 100
            assert len(spy_batch.call_args_list[2][0][0]) == 50
            assert len(vectors) == 250
            assert model == 'gemini'
