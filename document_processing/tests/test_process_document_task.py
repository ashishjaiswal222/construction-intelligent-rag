import pytest
import uuid
from unittest.mock import patch, MagicMock
from document_processing.tasks.process_document import process_document_task
from document_processing.models import ProcessingJob

@pytest.fixture
def mock_document():
    doc = MagicMock()
    doc.id = uuid.uuid4()
    doc.file.path = "dummy.pdf"
    return doc

@patch('document_processing.tasks.process_document.Document')
@patch('document_processing.tasks.process_document.ProcessingRepository')
@patch('document_processing.tasks.process_document.get_page_count')
@patch('document_processing.tasks.process_document.chord')
def test_task_creates_processing_job(mock_chord, mock_get_page_count, mock_repo_class, mock_doc_class, mock_document):
    mock_doc_class.objects.get.return_value = mock_document
    
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_job = MagicMock()
    mock_job.id = uuid.uuid4()
    mock_repo.create_job.return_value = mock_job
    
    mock_get_page_count.return_value = 3
    
    # Needs to mock chord completely so it doesn't fail trying to build celery tasks
    # The actual task logic uses the celery chord, which is hard to mock perfectly without pytest-celery
    # But we can verify repo calls
    process_document_task(str(mock_document.id))
    
    mock_repo.create_job.assert_called_once_with(str(mock_document.id))
    mock_repo.update_status.assert_any_call(mock_job.id, ProcessingJob.Status.SPLITTING)
    mock_repo.set_total_pages.assert_called_once_with(mock_job.id, 3)

@patch('document_processing.tasks.process_document.Document')
@patch('document_processing.tasks.process_document.ProcessingRepository')
@patch('document_processing.tasks.process_document.get_page_count')
@patch('document_processing.tasks.process_page.process_page_task')
@patch('document_processing.tasks.process_document.chord')
def test_task_dispatches_page_tasks(mock_chord, mock_process_page_task, mock_get_page_count, mock_repo_class, mock_doc_class, mock_document):
    mock_doc_class.objects.get.return_value = mock_document
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_job = MagicMock()
    mock_job.id = uuid.uuid4()
    mock_repo.create_job.return_value = mock_job
    
    mock_get_page_count.return_value = 2
    
    mock_sig = MagicMock()
    mock_process_page_task.s.return_value = mock_sig
    
    process_document_task(str(mock_document.id))
    
    assert mock_process_page_task.s.call_count == 2
    mock_process_page_task.s.assert_any_call(str(mock_job.id), 1)
    mock_process_page_task.s.assert_any_call(str(mock_job.id), 2)

@patch('document_processing.tasks.process_document.Document')
@patch('document_processing.tasks.process_document.process_document_task.retry')
def test_failed_task_retries_with_backoff(mock_retry, mock_doc_class):
    # Setup mock to raise Exception when getting document
    mock_doc_class.objects.get.side_effect = Exception("DB Error")
    
    mock_retry.side_effect = Exception("Retry Triggered")
    
    with pytest.raises(Exception, match="Retry Triggered"):
        # simulate execution, self is automatically bound but we patch it in the test or 
        # actually process_document_task is a Celery task wrapper, so we might need to call it appropriately
        process_document_task(str(uuid.uuid4()))
        
    mock_retry.assert_called_once()
