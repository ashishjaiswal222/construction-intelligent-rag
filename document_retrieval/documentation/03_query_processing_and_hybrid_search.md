# Document Retrieval: 03 Query Processing & Hybrid Search

This document details the mechanics of the first three stages of the pipeline: Self-Querying, Dense/Sparse Search, and RRF Fusion.

## 1. Self-Query Service

The `SelfQueryService` uses LangChain's `with_structured_output` to force an LLM (Groq `llama-3.1-8b`) to return a strict JSON schema (`QueryFilters`).

### Handling Edge Cases:
- **Missing Filters**: If a user just asks *"How deep is the foundation?"*, the LLM leaves `project_id` and `doc_type` as `None`.
- **The `is_current` Enforcer**: Construction is dangerous. If a user doesn't specify versioning, the pipeline *manually* overrides `is_current = None` to `is_current = True` inside `retrieval_pipeline.py`. To view old documents, a user must explicitly say *"Show me the superseded drawings."*
- **Sub-Query Generation**: Users often use the wrong terminology. The LLM generates 3 alternative phrasings (e.g., expanding "rebar" to "reinforcing bar") to maximize vector search surface area.

## 2. Dense Search (Qdrant)

The `DenseSearchService` connects to the local Qdrant instance.

### Payload Filtering
We do not use post-search filtering for Dense search. We use Qdrant's native `Filter(must=[...])` mechanics.
```python
conditions.append(
    FieldCondition(key='is_current', match=MatchValue(value=True))
)
```
**Why?** If we retrieve 15 chunks, and then filter out 14 of them in-memory because they are superseded, we are left with only 1 chunk. Native payload filtering ensures Qdrant only searches within the valid slice of data, guaranteeing we always get 15 valid chunks.

## 3. Sparse Search (BM25)

The `SparseSearchService` utilizes the `rank_bm25` library. 

### The Singleton Pattern
The BM25 index (created in Phase 6) is a massive pickled file (`construction_bm25_index.pkl`) containing the tokenized vocabulary of every document in the system.
- Loading this file takes ~200-500ms.
- To avoid this penalty on every API call, the `RetrievalPipeline` is instantiated globally in `api/views.py`. 
- When `SparseSearchService` initializes, it loads the pickle file into RAM once, providing 10ms keyword lookups for all subsequent API requests.

### In-Memory Filtering
Unlike Qdrant, BM25 does not support native payload filtering. 
Therefore, `SparseSearchService` retrieves the top 90 chunks (`top_k * 3`), and then loops through them in Python to manually strip out chunks that don't match the `project_id` or `is_current` flags, returning the cleanest top 30.

## 4. Reciprocal Rank Fusion (RRF)

We use the standard RRF mathematical formula to blend the Dense and Sparse results:

$$ RRF\_Score = \sum_{systems} \frac{1}{k + rank} $$

Where $k$ is a smoothing constant (set to 60). 

**Code Implementation:**
```python
for rank, chunk in enumerate(dense_results, 1):
    scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0) + 1.0 / (k + rank)
```

**The Benefit**: If a document has the exact phrasing the user asked for (scoring high in BM25) AND conceptually discusses the broader topic (scoring high in Qdrant), its RRF score aggregates rapidly, pushing it to the #1 spot.
