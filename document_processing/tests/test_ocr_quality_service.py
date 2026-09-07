import pytest
from document_processing.services.ocr.ocr_quality_service import OCRQualityService

@pytest.fixture
def quality_svc():
    return OCRQualityService()

def test_high_quality_text_scores_above_threshold(quality_svc):
    # Long text, good alpha ratio
    text = "This is a standard text from a document. " * 10
    score = quality_svc.calculate_quality(text, 0.95)
    assert score > 0.55
    assert score <= 1.0

def test_garbage_text_scores_below_threshold(quality_svc):
    # Short text with lots of symbols
    text = "!@#$%^&*()_+ " * 5
    score = quality_svc.calculate_quality(text, 0.4)
    assert score < 0.55

def test_empty_text_returns_zero(quality_svc):
    score = quality_svc.calculate_quality("", 0.0)
    assert score == 0.0
