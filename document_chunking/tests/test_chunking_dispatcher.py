import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from document_chunking.services.chunking_dispatcher import ChunkingDispatcher
from document_chunking.services.strategies.generic_strategy import GenericChunkingStrategy

@pytest.fixture
def dispatcher():
    return ChunkingDispatcher()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4())}

def test_routes_contract_to_contract_strategy(dispatcher, mock_meta):
    with patch('document_chunking.services.strategies.contract_strategy.ContractChunkingStrategy.chunk') as mock_chunk:
        dispatcher.dispatch('contract', 'text', str(uuid4()), 1, mock_meta)
        mock_chunk.assert_called_once()

def test_routes_boq_to_boq_strategy(dispatcher, mock_meta):
    with patch('document_chunking.services.strategies.boq_strategy.BOQChunkingStrategy.chunk') as mock_chunk:
        dispatcher.dispatch('boq', 'text', str(uuid4()), 1, mock_meta)
        mock_chunk.assert_called_once()

def test_routes_unknown_to_generic(dispatcher, mock_meta):
    with patch('document_chunking.services.strategies.generic_strategy.GenericChunkingStrategy.chunk') as mock_chunk:
        dispatcher.dispatch('unknown_type', 'text', str(uuid4()), 1, mock_meta)
        mock_chunk.assert_called_once()

def test_falls_back_to_generic_on_empty_result(dispatcher, mock_meta):
    with patch('document_chunking.services.strategies.contract_strategy.ContractChunkingStrategy.chunk', return_value=[]):
        chunks = dispatcher.dispatch('contract', 'Random text no clauses', str(uuid4()), 1, mock_meta)
        assert len(chunks) > 0
        assert chunks[0].chunk_type == 'generic'
        assert 'ContractChunkingStrategy returned no chunks' in chunks[0].metadata['fallback_reason']

def test_falls_back_to_generic_on_strategy_exception(dispatcher, mock_meta):
    with patch('document_chunking.services.strategies.contract_strategy.ContractChunkingStrategy.chunk', side_effect=Exception('Test Error')):
        chunks = dispatcher.dispatch('contract', 'Text', str(uuid4()), 1, mock_meta)
        assert len(chunks) > 0
        assert chunks[0].chunk_type == 'generic'
