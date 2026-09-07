import pytest
from unittest.mock import patch, MagicMock
from document_processing.services.drawing.drawing_understanding_service import DrawingUnderstandingService

@pytest.fixture
def drawing_service():
    with patch('google.generativeai.configure'), patch('google.generativeai.GenerativeModel'):
        return DrawingUnderstandingService()

@patch('PIL.Image.open')
def test_drawing_result_parsed_from_valid_json(mock_img_open, drawing_service):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    drawing_service.model.generate_content.return_value.text = '''```json
    {
      "drawing_number": "A-101",
      "sheet_number": "1 of 5",
      "revision": "B",
      "discipline": "Architectural",
      "title": "Floor Plan",
      "scale": "1:100",
      "grid_references": ["A1", "B2"],
      "notes": ["Note 1"],
      "dimensions": ["10m x 20m"],
      "title_block": {"Project": "Building A"},
      "revision_history": [{"rev": "A", "date": "2023-01-01", "description": "Initial", "approved_by": "J.D."}],
      "description": "This is a floor plan."
    }
    ```'''
    
    result = drawing_service.analyze_drawing("dummy.jpg", 1)
    
    assert result.drawing_number == "A-101"
    assert result.revision == "B"
    assert len(result.notes) == 1

@patch('PIL.Image.open')
def test_missing_fields_use_none_not_raise(mock_img_open, drawing_service):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    # Missing discipline, scale, title
    drawing_service.model.generate_content.return_value.text = '''
    {
      "drawing_number": "A-101",
      "sheet_number": null,
      "grid_references": [],
      "notes": [],
      "dimensions": [],
      "title_block": {},
      "revision_history": [],
      "description": ""
    }
    '''
    
    result = drawing_service.analyze_drawing("dummy.jpg", 1)
    
    assert result.drawing_number == "A-101"
    assert result.discipline is None
    assert result.scale is None

@patch('PIL.Image.open')
def test_invalid_json_returns_empty_drawing_result(mock_img_open, drawing_service):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    drawing_service.model.generate_content.return_value.text = '''Not JSON'''
    
    result = drawing_service.analyze_drawing("dummy.jpg", 1)
    
    assert result.confidence == 0.0
    assert result.drawing_number is None
