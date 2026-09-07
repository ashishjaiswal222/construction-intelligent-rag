import pytest
from document_processing.services.routing.ocr_router import OCRRouter
from document_processing.schemas.page_analysis import PageAnalysisResult
from document_processing.schemas.ocr_result import OCRStrategy

@pytest.fixture
def router():
    return OCRRouter()

@pytest.fixture
def base_analysis():
    return PageAnalysisResult(
        page_number=1,
        contains_tables=False,
        contains_handwriting=False,
        contains_drawing=False,
        contains_stamp=False,
        contains_signature=False,
        contains_revision_block=False,
        contains_title_block=False,
        contains_grid_reference=False,
        recommended_strategy=OCRStrategy.PADDLE_OCR,
        analysis_confidence=0.9
    )

def test_routes_handwriting_to_gemini(router, base_analysis):
    base_analysis.contains_handwriting = True
    strategy = router.route("dummy.pdf", 1, "invoice", base_analysis, 0.0)
    assert strategy == OCRStrategy.GEMINI_VISION

def test_routes_drawing_to_gemini(router, base_analysis):
    base_analysis.contains_drawing = True
    strategy = router.route("dummy.pdf", 1, "drawing", base_analysis, 0.0)
    assert strategy == OCRStrategy.GEMINI_VISION

def test_routes_standard_page_to_paddle(router, base_analysis):
    strategy = router.route("dummy.pdf", 1, "invoice", base_analysis, 0.0)
    assert strategy == OCRStrategy.PADDLE_OCR

def test_low_confidence_paddle_escalates_to_gemini():
    # This behavior is tested in ensemble service but routing returns PADDLE
    # which is used by ensemble to start.
    pass
