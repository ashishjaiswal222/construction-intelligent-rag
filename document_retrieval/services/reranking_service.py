import logging
from document_retrieval.schemas.retrieval_result import RetrievedChunk

logger = logging.getLogger(__name__)

class RerankingService:
    def __init__(self, cohere_api_key: str):
        import cohere
        self.client = cohere.Client(cohere_api_key) if cohere_api_key else None
        self._circuit_open = False
        self._failure_count = 0
        self._circuit_threshold = 3

    def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 8,
    ) -> list[RetrievedChunk]:
        """
        Cohere cross-encoder reranking.
        Falls back to score-order if:
          - No API key configured
          - Circuit breaker is open (3+ consecutive failures)
          - Cohere returns 429 (quota exhausted)
        NEVER raises.
        """
        if not chunks:
            return []
            
        if not self.client:
            return chunks[:top_k]

        if self._circuit_open:
            logger.warning(
                'Cohere circuit open. Returning top-k by RRF score.'
            )
            return chunks[:top_k]

        try:
            texts = [c.content[:1200] for c in chunks]
            result = self.client.rerank(
                query=query,
                documents=texts,
                top_n=top_k,
                model='rerank-english-v3.0',
            )
            self._failure_count = 0
            return [chunks[r.index] for r in result.results]

        except Exception as e:
            self._failure_count += 1
            if self._failure_count >= self._circuit_threshold:
                self._circuit_open = True
                logger.error(
                    f'Cohere circuit opened after {self._failure_count} '
                    f'failures. Last error: {e}'
                )
            else:
                logger.warning(
                    f'Cohere rerank failed (attempt {self._failure_count})'
                    f': {e}. Using score order.'
                )
            return chunks[:top_k]
