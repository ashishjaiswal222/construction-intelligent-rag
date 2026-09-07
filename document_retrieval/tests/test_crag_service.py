import pytest
from unittest.mock import patch, MagicMock
from document_retrieval.services.crag_service import CRAGService
from document_retrieval.schemas.retrieval_result import RetrievedChunk
from document_retrieval.schemas.relevance_grade import RelevanceGrade, BatchRelevanceGrade

def make_chunk(chunk_id: str, content: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        doc_type="drawing",
        document_id="doc1",
        project_id="proj1",
        filename="draw.pdf",
        revision="A",
        is_current=True,
        chunk_type="generic",
        score=0.0
    )

class TestCRAGService:
    @patch('langchain_groq.ChatGroq')
    def test_relevant_chunk_included(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.return_value = BatchRelevanceGrade(grades=[
            RelevanceGrade(chunk_id="c1", is_relevant=True, confidence=0.9, reason="Direct answer")
        ])
        
        service = CRAGService("dummy_key")
        chunks = [make_chunk("c1", "This is the answer")]
        
        relevant, needs_fallback = service.grade_and_filter("query", chunks)
        
        assert len(relevant) == 1
        assert needs_fallback is False

    @patch('langchain_groq.ChatGroq')
    def test_irrelevant_chunk_excluded(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.return_value = BatchRelevanceGrade(grades=[
            RelevanceGrade(chunk_id="c1", is_relevant=False, confidence=0.8, reason="Unrelated")
        ])
        
        service = CRAGService("dummy_key")
        chunks = [make_chunk("c1", "Not the answer")]
        
        relevant, needs_fallback = service.grade_and_filter("query", chunks)
        
        assert len(relevant) == 0
        assert needs_fallback is True

    @patch('langchain_groq.ChatGroq')
    def test_needs_fallback_true_when_all_rejected(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.return_value = BatchRelevanceGrade(grades=[
            RelevanceGrade(chunk_id="c1", is_relevant=False, confidence=0.9, reason="Nope"),
            RelevanceGrade(chunk_id="c2", is_relevant=False, confidence=0.9, reason="Nope")
        ])
        
        service = CRAGService("dummy_key")
        chunks = [make_chunk("c1", "Bad"), make_chunk("c2", "Worse")]
        
        relevant, needs_fallback = service.grade_and_filter("query", chunks)
        
        assert len(relevant) == 0
        assert needs_fallback is True

    @patch('langchain_groq.ChatGroq')
    def test_includes_chunk_on_grading_exception(self, mock_chat_groq):
        mock_llm = MagicMock()
        mock_chat_groq.return_value = mock_llm
        mock_grader = MagicMock()
        mock_llm.with_structured_output.return_value = mock_grader
        
        mock_grader.invoke.side_effect = Exception("Groq failed")
        
        service = CRAGService("dummy_key")
        chunks = [make_chunk("c1", "Good info potentially")]
        
        relevant, needs_fallback = service.grade_and_filter("query", chunks)
        
        assert len(relevant) == 1
        assert needs_fallback is False
