from document_retrieval.schemas.retrieval_result import RetrievedChunk
from document_retrieval.repositories.retrieval_repository import RetrievalRepository

class ExpansionService:
    def __init__(self, repository: RetrievalRepository):
        self.repo = repository

    def expand(
        self,
        chunks: list[RetrievedChunk],
        max_parents: int = 5,
    ) -> list[RetrievedChunk]:
        """
        For contract chunks: if chunk is a contract_clause,
        fetch the parent chunk via raw SQL.
        Instead of appending it, PREPEND the parent text to the
        child chunk's content so they are ranked and evaluated 
        as a single, cohesive context block.
        """
        # We need to make deep copies so we don't modify the original chunks
        # if they are cached or used elsewhere.
        expanded = [c.model_copy() for c in chunks]
        parents_fetched = 0

        for chunk in expanded:
            if parents_fetched >= max_parents:
                break
            if chunk.chunk_type != 'contract_clause':
                continue

            parent = self.repo.get_parent_chunk(chunk.chunk_id)
            if parent:
                # Merge the parent text directly into this chunk's content
                chunk.content = f"{parent.content}\n\n{chunk.content}"
                parents_fetched += 1

        return expanded
