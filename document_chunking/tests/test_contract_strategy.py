import pytest
from uuid import uuid4
from document_chunking.services.strategies.contract_strategy import ContractChunkingStrategy

@pytest.fixture
def strategy():
    return ContractChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_splits_at_clause_boundaries(strategy, mock_meta):
    text = "1. Introduction\nThis is intro.\n2. Scope\nThis is scope.\n2.1 Details\nDetails here."
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 3
    assert chunks[0].metadata['clause_number'] == '1.'
    assert chunks[1].metadata['clause_number'] == '2.'
    assert chunks[2].metadata['clause_number'] == '2.1'

def test_includes_parent_clause_in_deep_chunk(strategy, mock_meta):
    text = "1. Main\n1.1 Sub\n1.1.1 Deep\nDeep text here."
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 3
    assert chunks[2].metadata['clause_number'] == '1.1.1'
    assert chunks[2].metadata['parent_clause'] == '1.1'
    assert '[Parent: Clause 1.1]' in chunks[2].content

def test_never_splits_single_clause_even_if_long(strategy, mock_meta):
    text = "1. Long\n" + "A" * 4000
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 1
    assert chunks[0].char_count > 4000

def test_falls_back_to_generic_if_no_clause_pattern(strategy, mock_meta):
    text = "No clauses here.\nJust text."
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    # The strategy itself just returns 0 chunks, dispatcher handles fallback
    assert len(chunks) == 0
