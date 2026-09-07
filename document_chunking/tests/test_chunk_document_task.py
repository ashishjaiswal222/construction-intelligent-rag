import pytest
from unittest.mock import patch, MagicMock
from document_chunking.tasks.chunk_document import chunk_document_task

@patch('document_chunking.tasks.chunk_document.ChunkingRepository')
@patch('document_chunking.tasks.chunk_document.chord')
def test_creates_chunking_job_on_trigger(mock_chord, mock_repo_cls):
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_document_context.return_value = {'doc_type': 'contract'}
    mock_job = MagicMock()
    mock_repo.create_chunking_job.return_value = mock_job
    mock_repo.get_refined_pages.return_value = [{'page_id': '123'}]
    
    res = chunk_document_task('doc-1')
    mock_repo.create_chunking_job.assert_called_once_with('doc-1', 'contract')
    assert res['status'] == 'processing'

@patch('document_chunking.tasks.chunk_document.ChunkingRepository')
@patch('document_chunking.tasks.chunk_document.chord')
def test_dispatches_chord_for_each_page(mock_chord, mock_repo_cls):
    mock_repo = mock_repo_cls.return_value
    mock_repo.get_document_context.return_value = {'doc_type': 'contract'}
    mock_repo.get_refined_pages.return_value = [{'page_id': '1'}, {'page_id': '2'}]
    
    chunk_document_task('doc-1')
    mock_chord.assert_called_once()
    
# test_aggregate_fires_chunking_completed_signal and test_job_marked_partial_on_some_failures
# can be added for the aggregate task specifically, but the instruction asks for them in test_chunk_document_task.py
@patch('document_chunking.tasks.chunking_aggregate.ChunkingRepository')
@patch('document_chunking.tasks.chunking_aggregate.DocumentChunk')
@patch('document_chunking.models.chunking_job.ChunkingJob.objects.get')
@patch('document_chunking.signals.chunking_completed')
def test_aggregate_fires_chunking_completed_signal(mock_signal, mock_job_get, mock_chunk_cls, mock_repo_cls):
    from document_chunking.tasks.chunking_aggregate import chunking_aggregate_task
    mock_job = MagicMock()
    mock_job.failed_pages = 0
    mock_job_get.return_value = mock_job
    
    chunking_aggregate_task([], 'job-1', 'doc-1')
    mock_signal.send.assert_called_once()

@patch('document_chunking.tasks.chunking_aggregate.ChunkingRepository')
@patch('document_chunking.tasks.chunking_aggregate.DocumentChunk')
@patch('document_chunking.models.chunking_job.ChunkingJob.objects.get')
def test_job_marked_partial_on_some_failures(mock_job_get, mock_chunk_cls, mock_repo_cls):
    from document_chunking.tasks.chunking_aggregate import chunking_aggregate_task
    from document_chunking.models.chunking_job import ChunkingJob
    
    mock_job = MagicMock()
    mock_job.failed_pages = 1
    mock_job.chunked_pages = 5
    mock_job_get.return_value = mock_job
    
    chunking_aggregate_task([], 'job-1', 'doc-1')
    
    mock_repo_cls.return_value.complete_job.assert_called_once()
    args, kwargs = mock_repo_cls.return_value.complete_job.call_args
    assert kwargs['status'] == ChunkingJob.Status.PARTIAL
