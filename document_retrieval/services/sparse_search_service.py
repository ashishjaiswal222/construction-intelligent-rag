import logging
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.schemas.retrieval_result import RetrievedChunk

logger = logging.getLogger(__name__)

class SparseSearchService:
    def __init__(self, bm25_index_path: str):
        self.bm25_path = bm25_index_path
        self._index = None
        self._doc_ids = []
        self._load()

    def _load(self) -> None:
        """Load BM25 index from disk and reconstruct Okapi index. Silent on failure."""
        import pickle, os
        from rank_bm25 import BM25Okapi
        if not os.path.exists(self.bm25_path):
            return
        try:
            with open(self.bm25_path, 'rb') as f:
                data = pickle.load(f)
                self._doc_ids = data.get('doc_ids', [])
                corpus = data.get('corpus', [])
                if corpus:
                    self._index = BM25Okapi(corpus)
        except Exception as e:
            logger.warning(
                f'BM25 load failed: {e}. Sparse search disabled.'
            )

    def search(
        self,
        query: str,
        filters: QueryFilters,
        top_k: int = 30,
    ) -> list[RetrievedChunk]:
        """
        BM25 keyword search.
        Fetches metadata using SQL with native filtering for speed.
        Returns empty list if index not loaded.
        """
        if self._index is None or not self._doc_ids:
            return []

        import numpy as np
        from document_retrieval.repositories.retrieval_repository import RetrievalRepository
        
        tokens = query.lower().split()
        scores = self._index.get_scores(tokens)
        
        # Grab top_k * 3 just in case many are filtered out
        top_indices = np.argsort(scores)[::-1][:top_k * 3]

        candidate_ids = []
        candidate_scores = {}
        for i in top_indices:
            if scores[i] > 0:
                chunk_id = self._doc_ids[i]
                candidate_ids.append(chunk_id)
                candidate_scores[chunk_id] = scores[i]

        if not candidate_ids:
            return []
            
        repo = RetrievalRepository()
        filtered_chunks = repo.get_chunks_by_ids(candidate_ids, filters)
        
        # Apply the BM25 scores to the hydrated chunks and sort them properly
        for chunk in filtered_chunks:
            chunk.score = candidate_scores.get(chunk.chunk_id, 0.0)
            
        filtered_chunks.sort(key=lambda c: c.score, reverse=True)
        return filtered_chunks[:top_k]
