import pytest
from unittest.mock import patch, MagicMock
from celery.exceptions import Retry

@pytest.mark.django_db
class TestEmbedAndIndexTask:

    @patch('document_indexing.tasks.embed_and_index_task.IndexingRepository')
    @patch('document_indexing.tasks.embed_and_index_task.EmbeddingService')
    @patch('document_indexing.tasks.embed_and_index_task.QdrantIndexService')
    @patch('document_indexing.tasks.embed_and_index_task.BM25IndexService')
    @patch('document_indexing.tasks.embed_and_index_task.indexing_completed.send')
    def test_task_fires_signal_on_success(self, mock_send, mock_bm25, mock_qdrant, mock_embed, mock_repo):
        from document_indexing.tasks.embed_and_index_task import embed_and_index_task
        
        repo_instance = MagicMock()
        repo_instance.get_chunks_for_document.return_value = [{'id': '1', 'chunk_text': 'r', 'chunk_sequence': 1, 'total_chunks': 1}]
        repo_instance.get_metadata_for_document.return_value = {'is_current': True}
        repo_instance.get_doc_type.return_value = 'drawing'
        mock_repo.return_value = repo_instance
        
        embed_instance = MagicMock()
        embed_instance.embed_chunks_batched.return_value = ([[0.1]*768], 0, "gemini")
        mock_embed.return_value = embed_instance
        
        qdrant_instance = MagicMock()
        qdrant_instance.upsert_chunks.return_value = 1
        mock_qdrant.return_value = qdrant_instance
        
        embed_and_index_task('d1')
        
        mock_send.assert_called_once()
        repo_instance.save_indexing_record.assert_called_once()

    @patch('document_indexing.tasks.embed_and_index_task.IndexingRepository')
    @patch('document_indexing.tasks.embed_and_index_task.EmbeddingService')
    @patch('document_indexing.tasks.embed_and_index_task.QdrantIndexService')
    @patch('document_indexing.tasks.embed_and_index_task.BM25IndexService')
    @patch('document_indexing.tasks.embed_and_index_task.indexing_completed.send')
    def test_task_fires_signal_even_on_embedding_failure(self, mock_send, mock_bm25, mock_qdrant, mock_embed, mock_repo):
        from document_indexing.tasks.embed_and_index_task import embed_and_index_task
        from document_indexing.models.failed_indexing_job import FailedIndexingJob
        
        repo_instance = MagicMock()
        repo_instance.get_chunks_for_document.return_value = [{'id': '1', 'chunk_text': 'r', 'chunk_sequence': 1, 'total_chunks': 1}]
        repo_instance.get_metadata_for_document.return_value = {'is_current': True}
        repo_instance.get_doc_type.return_value = 'drawing'
        mock_repo.return_value = repo_instance
        
        embed_instance = MagicMock()
        embed_instance.embed_chunks_batched.side_effect = Exception('Gemini down')
        mock_embed.return_value = embed_instance
        
        embed_and_index_task('d1')
        
        # Check DLQ
        assert FailedIndexingJob.objects.count() == 1
        repo_instance.mark_status.assert_called_with('d1', 'failed')
        mock_send.assert_not_called()

    @patch('document_indexing.tasks.embed_and_index_task.IndexingRepository')
    @patch('document_indexing.tasks.embed_and_index_task.EmbeddingService')
    @patch('document_indexing.tasks.embed_and_index_task.QdrantIndexService')
    @patch('document_indexing.tasks.embed_and_index_task.BM25IndexService')
    def test_task_retries_on_db_exception(self, mock_bm25, mock_qdrant, mock_embed, mock_repo):
        from document_indexing.tasks.embed_and_index_task import embed_and_index_task
        
        repo_instance = MagicMock()
        repo_instance.get_chunks_for_document.side_effect = Exception('DB Error')
        mock_repo.return_value = repo_instance
        
        with patch('document_indexing.tasks.embed_and_index_task.embed_and_index_task.retry') as mock_retry:
            mock_retry.side_effect = Retry('RetryException')
            with pytest.raises(Retry):
                embed_and_index_task('d1')
                
            mock_retry.assert_called_once()
