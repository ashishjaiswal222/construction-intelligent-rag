# Qdrant and BM25 Design

## 1. Dual-Index Approach
We use a **Hybrid Search Strategy**, meaning we write to two different systems simultaneously.

### Qdrant Vector DB (Dense Search)
- **Role:** Understands meaning and conceptual similarity.
- **Why Qdrant?** Qdrant is faster, has lower memory consumption, and supports richer payload filtering than Chroma. It is excellent for handling complex metadata filtering over millions of vectors.
- **Local Storage:** Configured via `qdrant_client` locally pointing to `./construction_qdrant_db/`. No Docker required for local development.
- **Idempotency:** Qdrant enforces uniqueness using the `chunk_id` string. If a chunk is processed twice, it overwrites the existing point rather than duplicating.
- **Distance Metric:** Cosine similarity.

### BM25 Sparse Index (Exact Keyword Match)
- **Role:** Finds exact words, part numbers, and IDs that embedding models often misunderstand.
- **Implementation:** Custom in-memory wrapper using `rank_bm25`.
- **Concurrency:** Thread-safe operations using `threading.Lock()` to prevent race conditions during Celery worker writes.
- **Persistence:** Periodically serialized to disk via `pickle` at `./construction_bm25_index.pkl`.

## 2. Routing Logic
When a query enters the system in Phase 7, it will evaluate the query intent:
1. **Is it a specific ID, part number, or precise term?** Weight BM25 higher.
2. **Is it a conceptual question (e.g., "how should the concrete be poured?")?** Weight Qdrant higher.
3. Both sets of results are fetched, combined via Reciprocal Rank Fusion (RRF), and returned as the ultimate Context for generation.
