from typing import Tuple, List
from document_retrieval.schemas.retrieval_result import RetrievedChunk
from rag_generation.schemas.citation import Citation

class ContextBuilder:
    """
    Converts a list of RetrievedChunk objects into a formatted
    context string ready for injection into the generation prompt.
    """

    MAX_CONTEXT_CHARS = 6000

    def build(
        self,
        chunks: List[RetrievedChunk],
        user_query: str,
    ) -> Tuple[str, List[Citation]]:
        """
        Returns:
          context_string: formatted multi-source context block
          citations: ordered Citation list (index 0 = [1] in answer)
        """
        if not chunks:
            return "", []

        # Sort chunks by score descending
        sorted_chunks = sorted(chunks, key=lambda c: getattr(c, 'score', 0.0), reverse=True)
        
        context_string = ""
        citations = []
        current_chars = 0
        
        for i, chunk in enumerate(sorted_chunks):
            source_index = i + 1
            citation = self._make_citation(chunk, source_index)
            
            # Format the chunk
            header = f"[SOURCE {source_index}] {chunk.doc_type} | {chunk.filename} | Rev {chunk.revision}"
            if chunk.drawing_number:
                header += f" | Dwg: {chunk.drawing_number}"
            if getattr(chunk, 'clause_number', None):
                header += f" | Clause: {chunk.clause_number}"
                
            chunk_text = f"{header}\n{chunk.content}\n---\n"
            
            # Check budget
            if current_chars + len(chunk_text) > self.MAX_CONTEXT_CHARS:
                # Truncate content slightly if we can fit part of it
                remaining = self.MAX_CONTEXT_CHARS - current_chars
                if remaining > 200:
                    truncated_content = chunk.content[:remaining-100] + "..."
                    chunk_text = f"{header}\n{truncated_content}\n---\n"
                    context_string += chunk_text
                    citations.append(citation)
                break
                
            context_string += chunk_text
            citations.append(citation)
            current_chars += len(chunk_text)
            
        return context_string, citations

    def _make_citation(
        self,
        chunk: RetrievedChunk,
        index: int,
    ) -> Citation:
        """
        Build a Citation from a RetrievedChunk.
        """
        excerpt = chunk.content[:200].strip() if chunk.content else ""
        return Citation(
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            filename=chunk.filename,
            doc_type=chunk.doc_type,
            page_number=getattr(chunk, 'page_number', None),
            drawing_number=chunk.drawing_number,
            clause_number=getattr(chunk, 'clause_number', None),
            revision=chunk.revision,
            excerpt=excerpt
        )
