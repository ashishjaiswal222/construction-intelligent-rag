import pytest
from unittest.mock import patch, MagicMock
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.services.self_query_service import SelfQueryService

class TestSelfQueryService:
    @patch('langchain_groq.ChatGroq')
    def test_extracts_project_id_from_query(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        
        expected_filters = QueryFilters(
            project_id="PROJ-123",
            semantic_query="what is the foundation depth",
            sub_queries=["depth of foundation", "foundation specs", "how deep is foundation"]
        )
        mock_structured.invoke.return_value = expected_filters
        
        service = SelfQueryService("dummy_key")
        result = service.extract_filters("what is the foundation depth for PROJ-123")
        
        assert result.project_id == "PROJ-123"
        assert result.semantic_query == "what is the foundation depth"

    @patch('langchain_groq.ChatGroq')
    def test_sets_is_current_true_for_latest_keyword(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        
        expected_filters = QueryFilters(
            is_current=True,
            semantic_query="show me the latest plumbing plans",
            sub_queries=["current plumbing drawings", "approved plumbing", "IFC plumbing"]
        )
        mock_structured.invoke.return_value = expected_filters
        
        service = SelfQueryService("dummy_key")
        result = service.extract_filters("show me the latest plumbing plans")
        
        assert result.is_current is True

    @patch('langchain_groq.ChatGroq')
    def test_returns_minimal_filters_on_groq_exception(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        mock_structured.invoke.side_effect = Exception("Groq API timeout")
        
        service = SelfQueryService("dummy_key")
        query = "what is the concrete mix?"
        result = service.extract_filters(query)
        
        assert result.semantic_query == query
        assert len(result.sub_queries) == 3
        assert result.sub_queries == [query, query, query]

    @patch('langchain_groq.ChatGroq')
    def test_generates_three_sub_queries(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_structured = MagicMock()
        mock_llm.with_structured_output.return_value = mock_structured
        
        expected_filters = QueryFilters(
            semantic_query="rebar sizing",
            sub_queries=["rebar dimensions", "reinforcement size", "steel bar gauge"]
        )
        mock_structured.invoke.return_value = expected_filters
        
        service = SelfQueryService("dummy_key")
        result = service.extract_filters("what is the rebar sizing")
        
        assert len(result.sub_queries) == 3
