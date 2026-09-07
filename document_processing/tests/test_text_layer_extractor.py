import pytest
from unittest.mock import patch, MagicMock
from document_processing.services.text_layer.text_layer_extractor import TextLayerExtractor
from document_processing.schemas.ocr_result import OCRStrategy

@pytest.fixture
def extractor():
    return TextLayerExtractor()

@patch('fitz.open')
def test_good_text_layer_returns_text_layer_strategy(mock_fitz, extractor):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__getitem__.return_value = mock_page
    
    # 150 chars of good text
    good_text = "This is a very good text layer that should pass the heuristics easily since it has mostly alphabetic characters and no weird symbols " * 2
    mock_page.get_text.return_value = good_text
    mock_fitz.return_value = mock_doc

    text, quality, strategy = extractor.extract("dummy.pdf", 1)
    
    assert strategy == OCRStrategy.TEXT_LAYER
    assert quality > 0.85

@patch('fitz.open')
def test_low_char_count_falls_through(mock_fitz, extractor):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__getitem__.return_value = mock_page
    
    # < 100 chars
    mock_page.get_text.return_value = "Short text"
    mock_fitz.return_value = mock_doc

    text, quality, strategy = extractor.extract("dummy.pdf", 1)
    
    assert strategy is None
    assert quality == 0.0

@patch('fitz.open')
def test_garbage_text_falls_through(mock_fitz, extractor):
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_doc.__enter__.return_value = mock_doc
    mock_doc.__getitem__.return_value = mock_page
    
    # > 100 chars but garbage
    garbage_text = "" * 150
    mock_page.get_text.return_value = garbage_text
    mock_fitz.return_value = mock_doc

    text, quality, strategy = extractor.extract("dummy.pdf", 1)
    
    assert strategy is None
    assert quality < 0.85
