from document_retrieval.schemas.retrieval_result import RetrievedChunk
from document_retrieval.schemas.relevance_grade import BatchRelevanceGrade
from document_retrieval.prompts.crag_grading_prompt import CRAG_GRADING_PROMPT

class CRAGService:
    def __init__(self, groq_api_key: str):
        from langchain_groq import ChatGroq
        self.llm = ChatGroq(
            model='llama-3.1-8b-instant',
            api_key=groq_api_key,
            temperature=0.0,
        )

    def grade_and_filter(
        self,
        query: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[list[RetrievedChunk], bool]:
        """
        Grade chunks for relevance to the query using a single batch prompt.
        Returns (relevant_chunks, needs_fallback).
        needs_fallback=True when NO chunk passes grading.
        NEVER raises — on failure returns all chunks, needs_fallback=False.
        """
        if not chunks:
            return [], True

        grader = self.llm.with_structured_output(BatchRelevanceGrade)
        
        # Build the bundled extracts string
        extracts_str = ""
        for i, chunk in enumerate(chunks):
            extracts_str += f"--- Chunk ID: {chunk.chunk_id} ---\n{chunk.content[:400]}\n\n"

        try:
            batch_result = grader.invoke(
                CRAG_GRADING_PROMPT.format(
                    query=query,
                    extracts=extracts_str,
                )
            )
            
            # Map grades back to chunks
            grade_map = {g.chunk_id: g for g in batch_result.grades}
            
            relevant: list[RetrievedChunk] = []
            for chunk in chunks:
                grade = grade_map.get(chunk.chunk_id)
                if grade:
                    if grade.is_relevant and grade.confidence > 0.5:
                        relevant.append(chunk)
                else:
                    # If LLM missed a chunk, include it conservatively
                    relevant.append(chunk)
                    
        except Exception:
            # On total failure: return all chunks conservatively
            relevant = list(chunks)

        needs_fallback = len(relevant) == 0
        return relevant, needs_fallback
