import pytest
from unittest.mock import patch, MagicMock
from rag_generation.services.hallucination_guard import HallucinationGuard, HallucinationGuardResult

class TestHallucinationGuard:
    @patch('langchain_groq.ChatGroq')
    def test_returns_grounded_true_on_clean_answer(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.return_value = HallucinationGuardResult(is_grounded=True)
        
        guard = HallucinationGuard("dummy")
        is_grounded, warning = guard.check("query", "answer", "context")
        
        assert is_grounded is True
        assert warning is None

    @patch('langchain_groq.ChatGroq')
    def test_returns_grounded_false_with_warning_on_ungrounded_claim(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.return_value = HallucinationGuardResult(
            is_grounded=False, 
            warning="Danger"
        )
        
        guard = HallucinationGuard("dummy")
        is_grounded, warning = guard.check("query", "answer", "context")
        
        assert is_grounded is False
        assert warning == "Danger"

    @patch('langchain_groq.ChatGroq')
    def test_circuit_opens_after_three_groq_failures(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.side_effect = Exception("API down")
        
        guard = HallucinationGuard("dummy")
        
        guard.check("q", "a", "c")
        guard.check("q", "a", "c")
        
        assert guard._circuit_open is False
        
        guard.check("q", "a", "c")
        
        assert guard._circuit_open is True

    @patch('langchain_groq.ChatGroq')
    def test_circuit_open_returns_grounded_true_without_api_call(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        guard = HallucinationGuard("dummy")
        guard._circuit_open = True
        
        is_grounded, warning = guard.check("q", "a", "c")
        
        assert is_grounded is True
        assert mock_grader.invoke.called is False

    @patch('langchain_groq.ChatGroq')
    def test_never_raises_on_exception(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.side_effect = Exception("API down")
        
        guard = HallucinationGuard("dummy")
        is_grounded, warning = guard.check("q", "a", "c")
        
        assert is_grounded is True
