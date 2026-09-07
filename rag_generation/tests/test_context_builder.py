import pytest
from document_retrieval.schemas.retrieval_result import RetrievedChunk
from rag_generation.services.context_builder import ContextBuilder

def make_chunk(chunk_id="1", score=0.9, content="test content", filename="doc.pdf", doc_type="drawing", revision="A", drawing_number="DWG-01"):
    return RetrievedChunk(
        chunk_id=chunk_id,
        content=content,
        doc_type=doc_type,
        document_id="doc_id_1",
        project_id="proj_1",
        filename=filename,
        revision=revision,
        is_current=True,
        chunk_type="generic",
        score=score,
        drawing_number=drawing_number,
    )

class TestContextBuilder:
    def test_formats_chunk_with_source_label(self):
        builder = ContextBuilder()
        chunk = make_chunk()
        context, citations = builder.build([chunk], "query")
        
        assert "[SOURCE 1]" in context
        assert "doc.pdf" in context
        assert "Rev A" in context
        assert "DWG-01" in context
        assert "test content" in context
        assert len(citations) == 1
        assert citations[0].chunk_id == chunk.chunk_id

    def test_orders_chunks_by_score_descending(self):
        builder = ContextBuilder()
        c1 = make_chunk(chunk_id="1", score=0.5, content="low")
        c2 = make_chunk(chunk_id="2", score=0.9, content="high")
        
        context, citations = builder.build([c1, c2], "query")
        
        assert citations[0].chunk_id == "2"
        assert citations[1].chunk_id == "1"

    def test_trims_to_max_context_chars_dropping_lowest_scored(self):
        builder = ContextBuilder()
        builder.MAX_CONTEXT_CHARS = 100 # very small budget
        
        c1 = make_chunk(chunk_id="1", score=0.5, content="this is a long content string that takes up space")
        c2 = make_chunk(chunk_id="2", score=0.9, content="this is also long but scored higher")
        
        context, citations = builder.build([c1, c2], "query")
        
        assert len(citations) == 1
        assert citations[0].chunk_id == "2"

    def test_returns_empty_on_empty_chunk_list(self):
        builder = ContextBuilder()
        context, citations = builder.build([], "query")
        assert context == ""
        assert len(citations) == 0

    def test_citation_excerpt_is_200_chars_max(self):
        builder = ContextBuilder()
        long_content = "x" * 500
        chunk = make_chunk(content=long_content)
        context, citations = builder.build([chunk], "query")
        
        assert len(citations[0].excerpt) == 200

    def test_drawing_number_included_in_source_label_for_drawing_type(self):
        builder = ContextBuilder()
        chunk = make_chunk(doc_type="drawing", drawing_number="S-012")
        context, citations = builder.build([chunk], "query")
        assert "Dwg: S-012" in context
