import pytest
from unittest.mock import MagicMock
from rag_generation.schemas.generation_request import GenerationRequest
from rag_generation.services.generation_pipeline import GenerationPipeline
from rag_generation.schemas.citation import Citation
from document_retrieval.schemas.retrieval_result import RetrievalResult, RetrievedChunk

def make_chunk(cid, score):
    return RetrievedChunk(
        chunk_id=cid, content="x", doc_type="d", document_id="d1",
        project_id="p1", filename="f.pdf", revision="A", is_current=True,
        chunk_type="generic", score=score
    )

class TestGenerationPipeline:
    def setup_method(self):
        self.context_builder = MagicMock()
        self.generator = MagicMock()
        self.guard = MagicMock()
        self.repo = MagicMock()
        
        self.pipeline = GenerationPipeline(
            self.context_builder, self.generator, self.guard, self.repo
        )

    def test_full_pipeline_returns_generation_response(self):
        chunk = make_chunk("1", 0.9)
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=False, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("Context", [Citation(
            chunk_id="1", document_id="d1", filename="f.pdf", doc_type="d", revision="A", excerpt="x"
        )])
        self.generator.generate.return_value = "Answer"
        self.guard.check.return_value = (True, None)
        
        response = self.pipeline.generate(request)
        
        assert response.answer == "Answer"
        assert response.confidence == 0.9
        assert response.answer_grounded is True
        assert self.repo.save_log.called is True

    def test_empty_chunks_returns_failure_immediately_without_llm_call(self):
        retrieval_result = RetrievalResult(
            chunks=[], needs_fallback=True, filter_used={},
            candidates_found=0, final_count=0, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("", [])
        
        response = self.pipeline.generate(request)
        
        assert response.answer == "No relevant documents found."
        assert self.generator.generate.called is False
        assert response.confidence == 0.0
        assert response.answer_grounded is False

    def test_confidence_capped_at_0_6_when_needs_fallback(self):
        chunk = make_chunk("1", 0.9) # High score but fallback flag true
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=True, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("Context", [Citation(
            chunk_id="1", document_id="d1", filename="f.pdf", doc_type="d", revision="A", excerpt="x"
        )])
        self.generator.generate.return_value = "Answer"
        self.guard.check.return_value = (True, None)
        
        response = self.pipeline.generate(request)
        
        assert response.confidence == 0.6

    def test_warning_message_set_when_not_grounded(self):
        chunk = make_chunk("1", 0.9)
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=False, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("Context", [Citation(
            chunk_id="1", document_id="d1", filename="f.pdf", doc_type="d", revision="A", excerpt="x"
        )])
        self.generator.generate.return_value = "Answer"
        self.guard.check.return_value = (False, "Warning msg")
        
        response = self.pipeline.generate(request)
        
        assert response.answer_grounded is False
        assert response.warning_message == "Warning msg"

    def test_warning_message_set_when_needs_fallback(self):
        chunk = make_chunk("1", 0.9)
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=True, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("Context", [Citation(
            chunk_id="1", document_id="d1", filename="f.pdf", doc_type="d", revision="A", excerpt="x"
        )])
        self.generator.generate.return_value = "Answer"
        self.guard.check.return_value = (True, None) # Guard passes!
        
        response = self.pipeline.generate(request)
        
        assert response.answer_grounded is True
        assert "Answer may be incomplete" in response.warning_message

    def test_audit_log_saved_even_on_guard_failure(self):
        chunk = make_chunk("1", 0.9)
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=False, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.return_value = ("Context", [Citation(
            chunk_id="1", document_id="d1", filename="f.pdf", doc_type="d", revision="A", excerpt="x"
        )])
        self.generator.generate.return_value = "Answer"
        
        # Make the guard raise an unhandled exception
        self.guard.check.side_effect = Exception("Crash")
        
        response = self.pipeline.generate(request)
        
        assert "technical error" in response.answer
        assert self.repo.save_log.called is True

    def test_pipeline_never_raises(self):
        chunk = make_chunk("1", 0.9)
        retrieval_result = RetrievalResult(
            chunks=[chunk], needs_fallback=False, filter_used={},
            candidates_found=1, final_count=1, stages_completed=["stage"], processing_ms=100
        )
        request = GenerationRequest(user_query="Q", retrieval_result=retrieval_result)
        
        self.context_builder.build.side_effect = Exception("Builder crash")
        
        response = self.pipeline.generate(request)
        
        assert "technical error" in response.answer
