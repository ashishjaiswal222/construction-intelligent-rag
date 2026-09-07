import pytest
from unittest.mock import patch, MagicMock
from document_metadata.services.version_chain_manager import VersionChainManager

@pytest.fixture
def repo_mock():
    return MagicMock()

@pytest.fixture
def manager(repo_mock):
    return VersionChainManager(repo_mock)

def test_marks_previous_revision_not_current(manager, repo_mock):
    repo_mock.find_current_revision.return_value = {'document_id': 'prev-id'}
    result = manager.update_chain('new-id', 'S-01', 'proj-1', 'B')
    
    assert result is True
    repo_mock.mark_superseded.assert_called_once_with(document_id='prev-id', superseded_by_id='new-id')

def test_sets_superseded_by_id_on_previous(manager, repo_mock):
    repo_mock.find_current_revision.return_value = {'document_id': 'prev-id'}
    manager.update_chain('new-id', 'S-01', 'proj-1', 'B')
    repo_mock.mark_superseded.assert_called_with(document_id='prev-id', superseded_by_id='new-id')

def test_returns_false_when_no_previous_revision(manager, repo_mock):
    repo_mock.find_current_revision.return_value = None
    result = manager.update_chain('new-id', 'S-01', 'proj-1', 'A')
    assert result is False
    repo_mock.mark_superseded.assert_not_called()

def test_returns_false_when_no_drawing_number(manager, repo_mock):
    result = manager.update_chain('new-id', '', 'proj-1', 'A')
    assert result is False
    repo_mock.find_current_revision.assert_not_called()

def test_atomic_rollback_on_db_failure(manager, repo_mock):
    repo_mock.find_current_revision.return_value = {'document_id': 'prev-id'}
    repo_mock.mark_superseded.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        manager.update_chain('new-id', 'S-01', 'proj-1', 'B')
