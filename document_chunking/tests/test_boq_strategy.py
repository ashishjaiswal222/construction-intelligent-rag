import pytest
from uuid import uuid4
from document_chunking.services.strategies.boq_strategy import BOQChunkingStrategy

@pytest.fixture
def strategy():
    return BOQChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_produces_one_chunk_per_row(strategy, mock_meta):
    extracted = [{
        'rows': [
            {'item_number': '1.1', 'description': 'Concrete', 'quantity': 100, 'rate': 50},
            {'item_number': '1.2', 'description': 'Steel', 'quantity': 200, 'rate': 60}
        ]
    }]
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert len(chunks) == 2

def test_section_header_propagated_to_all_rows(strategy, mock_meta):
    extracted = [{
        'rows': [
            {'is_header': True, 'text': 'Section A'},
            {'item_number': '1.1', 'description': 'Concrete', 'quantity': 100, 'rate': 50},
            {'is_header': True, 'text': 'Division B'},
            {'item_number': '1.2', 'description': 'Steel', 'quantity': 200, 'rate': 60}
        ]
    }]
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert len(chunks) == 2
    assert chunks[0].metadata['boq_section'] == 'Section A'
    assert chunks[1].metadata['boq_section'] == 'Section A'
    assert chunks[1].metadata['boq_division'] == 'Division B'

def test_quantity_and_rate_in_separate_metadata_fields(strategy, mock_meta):
    extracted = [{
        'rows': [
            {'item_number': '1.1', 'description': 'Concrete', 'quantity': 100, 'rate': 50}
        ]
    }]
    chunks = strategy.chunk("", str(uuid4()), 1, mock_meta, extracted_data=extracted)
    assert chunks[0].metadata['quantity'] == '100'
    assert chunks[0].metadata['rate'] == '50'

def test_falls_back_to_generic_if_no_table_data(strategy, mock_meta):
    chunks = strategy.chunk("Some text", str(uuid4()), 1, mock_meta, extracted_data=None)
    assert len(chunks) == 0
