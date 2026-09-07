import pytest
from uuid import uuid4
from document_chunking.services.strategies.drawing_strategy import DrawingChunkingStrategy

@pytest.fixture
def strategy():
    return DrawingChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_produces_exactly_one_chunk_per_drawing(strategy, mock_meta):
    extracted = {'drawing_number': 'A-101'}
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert len(chunks) == 1

def test_drawing_number_in_metadata(strategy, mock_meta):
    extracted = {'drawing_number': 'A-101'}
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert chunks[0].metadata['drawing_number'] == 'A-101'

def test_is_current_true_for_ifc_status(strategy, mock_meta):
    extracted = {'drawing_number': 'A-101', 'status': 'IFC'}
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert chunks[0].metadata['is_current'] is True

def test_falls_back_to_generic_if_no_drawing_json(strategy, mock_meta):
    chunks = strategy.chunk("Some text", str(uuid4()), 1, mock_meta, extracted_data=None)
    assert len(chunks) == 0
