import pytest
from unittest.mock import patch, MagicMock
from document_metadata.services.metadata_extractor import MetadataExtractor
from document_metadata.schemas.extracted_metadata import ExtractedMetadata

@pytest.fixture
def extractor():
    with patch('document_metadata.services.metadata_extractor.ChatOllama') as mock_chatollama, \
         patch('document_metadata.services.metadata_extractor.ChatGroq') as mock_chatgroq:
        
        mock_ollama_instance = MagicMock()
        mock_chatollama.return_value = mock_ollama_instance
        
        mock_groq_instance = MagicMock()
        mock_chatgroq.return_value = mock_groq_instance
        
        ext = MetadataExtractor("fake_key")
        ext.ollama_mock = mock_ollama_instance
        ext.groq_mock = mock_groq_instance
        yield ext

def test_extracts_drawing_number_from_title_block_text(extractor):
    mock_result = ExtractedMetadata(drawing_number="S-023", revision="C")
    extractor.ollama_mock.with_structured_output.return_value.invoke.return_value = mock_result
    
    res = extractor.extract("Title Block Drawing S-023 Rev C", "drawing", "doc_id")
    assert res.drawing_number == "S-023"
    assert res.revision == "C"

def test_extracts_revision_from_text(extractor):
    mock_result = ExtractedMetadata(revision="Rev 03")
    extractor.ollama_mock.with_structured_output.return_value.invoke.return_value = mock_result
    
    res = extractor.extract("Revision: Rev 03", "contract", "doc_id")
    assert res.revision == "Rev 03"

def test_returns_confidence_zero_on_both_failures(extractor):
    extractor.ollama_mock.with_structured_output.return_value.invoke.side_effect = Exception("Ollama Error")
    extractor.groq_mock.with_structured_output.return_value.invoke.side_effect = Exception("Groq Error")
    
    res = extractor.extract("some text", "drawing", "doc_id")
    assert res.confidence == 0.0
    assert res.drawing_number is None

def test_falls_back_to_groq_on_ollama_failure(extractor):
    extractor.ollama_mock.with_structured_output.return_value.invoke.side_effect = Exception("Ollama Error")
    
    mock_result = ExtractedMetadata(drawing_number="FALLBACK-1")
    extractor.groq_mock.with_structured_output.return_value.invoke.return_value = mock_result
    
    res = extractor.extract("some text", "drawing", "doc_id")
    assert res.drawing_number == "FALLBACK-1"
    extractor.groq_mock.with_structured_output.return_value.invoke.assert_called_once()

def test_returns_empty_schema_not_raises_on_failure(extractor):
    extractor.ollama_mock.with_structured_output.return_value.invoke.side_effect = Exception("API Error")
    extractor.groq_mock.with_structured_output.return_value.invoke.side_effect = Exception("API Error")
    res = extractor.extract("some text", "drawing", "doc_id")
    assert isinstance(res, ExtractedMetadata)
    assert res.title is None

def test_validates_approval_status_rejects_invalid_value():
    res = ExtractedMetadata(approval_status="RandomStatus")
    assert res.approval_status is None
    
    res_valid = ExtractedMetadata(approval_status="IFC")
    assert res_valid.approval_status == "IFC"

def test_validates_discipline_rejects_invalid_value():
    res = ExtractedMetadata(discipline="random")
    assert res.discipline is None
    
    res_valid = ExtractedMetadata(discipline="STRUCTURAL")
    assert res_valid.discipline == "structural"

def test_confidence_higher_for_more_fields_found(extractor):
    res_few = ExtractedMetadata(drawing_number="S-1")
    res_few.confidence = extractor._calculate_confidence(res_few, "drawing")
    
    res_many = ExtractedMetadata(drawing_number="S-1", revision="A", discipline="structural", approval_status="IFC")
    res_many.confidence = extractor._calculate_confidence(res_many, "drawing")
    
    assert res_many.confidence > res_few.confidence

def test_temperature_zero_on_ollama_client():
    with patch('document_metadata.services.metadata_extractor.ChatOllama') as mock_chatollama:
        MetadataExtractor()
        mock_chatollama.assert_called_once()
        _, kwargs = mock_chatollama.call_args
        assert kwargs.get("temperature") == 0.0
