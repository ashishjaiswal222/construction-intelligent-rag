import pytest
from uuid import uuid4
from document_chunking.services.strategies.rfi_strategy import RFIChunkingStrategy

@pytest.fixture
def strategy():
    return RFIChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_question_and_answer_in_same_chunk(strategy, mock_meta):
    text = "RFI Number: 123\nQUESTION:\nWhat is this?\nRESPONSE:\nIt is that.\n"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 1
    assert 'QUESTION:\nWhat is this?' in chunks[0].content
    assert 'RESPONSE:\nIt is that.' in chunks[0].content

def test_is_answered_false_for_unanswered_rfi(strategy, mock_meta):
    text = "RFI Number: 123\nQUESTION:\nWhat is this?\nRESPONSE:\nNot yet responded\n"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 1
    assert chunks[0].metadata['is_answered'] is False

def test_falls_back_to_generic_if_no_rfi_pattern(strategy, mock_meta):
    text = "Just some random text."
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 0
