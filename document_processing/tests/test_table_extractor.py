import pytest
from unittest.mock import patch, MagicMock
from document_processing.services.table.table_extractor import TableExtractor

@pytest.fixture
def table_extractor():
    with patch('google.generativeai.configure'), patch('google.generativeai.GenerativeModel'):
        return TableExtractor()

@patch('PIL.Image.open')
def test_table_json_parsed_correctly(mock_img_open, table_extractor):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    table_extractor.model.generate_content.return_value.text = '''```json
    {
      "tables": [
        {
          "headers": ["Col 1", "Col 2"],
          "rows": [["Val 1", "Val 2"]],
          "merged_cells": [],
          "confidence": 0.95,
          "raw_markdown": "| Col 1 | Col 2 |\\n|---|---|\\n| Val 1 | Val 2 |"
        }
      ]
    }
    ```'''
    
    tables = table_extractor.extract_tables("dummy.jpg", 1)
    
    assert len(tables) == 1
    assert tables[0].headers == ["Col 1", "Col 2"]
    assert len(tables[0].rows) == 1

@patch('PIL.Image.open')
def test_merged_cells_preserved(mock_img_open, table_extractor):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    table_extractor.model.generate_content.return_value.text = '''
    {
      "tables": [
        {
          "headers": ["Col 1"],
          "rows": [["Val 1"]],
          "merged_cells": [{"row": 0, "col": 0, "rowspan": 2, "colspan": 1, "value": "Val 1"}],
          "confidence": 0.9,
          "raw_markdown": ""
        }
      ]
    }
    '''
    
    tables = table_extractor.extract_tables("dummy.jpg", 1)
    
    assert len(tables) == 1
    assert len(tables[0].merged_cells) == 1
    assert tables[0].merged_cells[0]['rowspan'] == 2

@patch('PIL.Image.open')
def test_invalid_gemini_response_returns_empty_list(mock_img_open, table_extractor):
    mock_img = MagicMock()
    mock_img_open.return_value = mock_img
    
    table_extractor.model.generate_content.return_value.text = '''
    Just some random text without JSON
    '''
    
    tables = table_extractor.extract_tables("dummy.jpg", 1)
    
    assert len(tables) == 0
