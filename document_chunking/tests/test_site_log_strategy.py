import pytest
from uuid import uuid4
from document_chunking.services.strategies.site_log_strategy import SiteLogChunkingStrategy

@pytest.fixture
def strategy():
    return SiteLogChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_splits_at_date_boundaries(strategy, mock_meta):
    text = "Date: 12/05/2023\nWeather: Sunny\nDate: 13/05/2023\nWeather: Rain"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 2

def test_single_entry_produces_one_chunk(strategy, mock_meta):
    text = "Date: 12/05/2023\nWeather: Sunny\nACTIVITIES:\nDigging"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 1

def test_date_in_metadata(strategy, mock_meta):
    text = "Date: 12/05/2023\nWeather: Sunny"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert chunks[0].metadata['log_date'] == '12/05/2023'
