from document_retrieval.schemas.retrieval_result import RetrievedChunk

class FusionService:
    def rrf_fuse(
        self,
        dense_results: list[RetrievedChunk],
        sparse_results: list[RetrievedChunk],
        k: int = 60,
        top_k: int = 40,
    ) -> list[RetrievedChunk]:
        """
        Reciprocal Rank Fusion.
        Formula: score = 1 / (k + rank) for each list.
        Sum scores across both lists.
        Return top_k by combined score.
        """
        scores: dict[str, float] = {}
        chunk_map: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(dense_results, 1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) \
                + 1.0 / (k + rank)
            chunk_map[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(sparse_results, 1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) \
                + 1.0 / (k + rank)
            chunk_map[chunk.chunk_id] = chunk

        sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)

        result = []
        for cid in sorted_ids[:top_k]:
            chunk = chunk_map[cid]
            # Update score to RRF score for transparency
            chunk = chunk.model_copy(
                update={'score': round(scores[cid], 6)}
            )
            result.append(chunk)
        return result
