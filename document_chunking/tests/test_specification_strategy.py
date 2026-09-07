import pytest
from uuid import uuid4
from document_chunking.services.strategies.specification_strategy import SpecificationChunkingStrategy

@pytest.fixture
def strategy():
    return SpecificationChunkingStrategy()

@pytest.fixture
def mock_meta():
    return {'document_id': str(uuid4()), 'project_id': 'proj-123'}

def test_splits_at_section_boundaries(strategy, mock_meta):
    text = "SECTION 1 GENERAL\nIntro\nSECTION 2 MATERIALS\nSteel"
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) == 2
    assert chunks[0].metadata['section_name'] == 'SECTION 1 GENERAL'
    assert chunks[1].metadata['section_name'] == 'SECTION 2 MATERIALS'

def test_long_section_split_with_overlap(strategy, mock_meta):
    text = "SECTION 1 GENERAL\n" + "A" * 2000
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    assert len(chunks) > 1
    assert chunks[0].metadata['section_name'] == 'SECTION 1 GENERAL'
    assert chunks[1].metadata['section_name'] == 'SECTION 1 GENERAL'
    assert chunks[1].metadata['chunk_part'] == 2

def test_section_name_in_every_chunk_content(strategy, mock_meta):
    text = "SECTION 1 GENERAL\n" + "A" * 2000
    chunks = strategy.chunk(text, str(uuid4()), 1, mock_meta)
    for chunk in chunks:
        assert 'Section: SECTION 1 GENERAL' in chunk.content
