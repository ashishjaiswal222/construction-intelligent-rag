import pytest
from unittest.mock import patch, MagicMock
from rag_generation.services.generator_service import GeneratorService

class TestGeneratorService:
    @patch('langchain_groq.ChatGroq')
    def test_calls_groq_with_formatted_prompt(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="answer")
        mock_chat_groq.return_value = mock_llm

        service = GeneratorService("dummy")
        result = service.generate("query", "context string", False)

        assert result == "answer"
        assert mock_llm.invoke.called
        args, _ = mock_llm.invoke.call_args
        assert "context string" in args[0]
        assert "query" in args[0]
        assert "An exact match for the user's query was not found" not in args[0]

    @patch('langchain_groq.ChatGroq')
    def test_uses_fallback_prompt_when_needs_fallback_true(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="answer")
        mock_chat_groq.return_value = mock_llm

        service = GeneratorService("dummy")
        result = service.generate("query", "context string", True)

        args, _ = mock_llm.invoke.call_args
        assert "An exact match for the user's query was not found" in args[0]

    @patch('langchain_groq.ChatGroq')
    def test_returns_failure_message_on_groq_exception(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = Exception("API down")
        mock_chat_groq.return_value = mock_llm

        service = GeneratorService("dummy")
        result = service.generate("query", "context string", False)

        assert result == GeneratorService.FAILURE_MESSAGE

    @patch('langchain_groq.ChatGroq')
    def test_temperature_is_0_point_1(self, mock_chat_groq):
        service = GeneratorService("dummy")
        mock_chat_groq.assert_called_with(
            model='llama-3.1-8b-instant',
            api_key='dummy',
            temperature=0.1,
            max_tokens=1024
        )
