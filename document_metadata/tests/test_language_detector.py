import pytest
from unittest.mock import patch
from document_metadata.services.language_detector import LanguageDetector

@pytest.fixture
def detector():
    return LanguageDetector()

def test_detects_english_text(detector):
    text = "This is a standard engineering drawing with notes in English." * 10
    with patch('langdetect.detect', return_value='en'):
        assert detector.detect(text) == 'en'

def test_detects_hindi_text(detector):
    text = "यह एक मानक इंजीनियरिंग आरेखण है जिसमें हिंदी में नोट्स हैं।" * 10
    with patch('langdetect.detect', return_value='hi'):
        assert detector.detect(text) == 'hi'

def test_detects_mixed_english_hindi(detector):
    text = "Standard drawing notes. यह एक मानक आरेखण है।" * 10
    with patch('langdetect.detect', return_value='en'):
        assert detector.detect(text) == 'mixed'

def test_returns_unknown_for_text_under_50_chars(detector):
    assert detector.detect("Too short") == 'unknown'

def test_returns_unknown_on_langdetect_exception(detector):
    text = "Standard engineering drawing notes." * 10
    with patch('langdetect.detect', side_effect=Exception("Detection error")):
        assert detector.detect(text) == 'unknown'

def test_detects_urdu_as_hindi(detector):
    text = "Standard engineering drawing notes." * 10
    with patch('langdetect.detect', return_value='ur'):
        assert detector.detect(text) == 'hi'
