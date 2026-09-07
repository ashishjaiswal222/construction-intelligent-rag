# Document Retrieval: 05 Schemas, API, and Tests

This document covers the data structures, the exposed API, and the testing strategy that ensures 100% reliability of the retrieval pipeline.

## 1. Pydantic v2 Schemas

We enforce `ConfigDict(extra='forbid')` on all schemas. This ensures that no loose JSON data or unexpected LLM hallucinations can pollute our strict data pipeline.

### `QueryFilters`
The output of Stage 1 (Self-Querying). 
```python
class QueryFilters(BaseModel):
    model_config = ConfigDict(extra='forbid')
    project_id:     Optional[str] = None
    doc_type:       Optional[str] = None
    is_current:     Optional[bool] = None
    semantic_query: str
    sub_queries:    list[str]
```

### `RetrievalResult`
The final payload sent back to the API. It contains performance metrics, the actual text chunks, and the `needs_fallback` boolean flag. If `needs_fallback` is True, it tells the frontend (or Phase 8 Generator) to warn the user: *"I couldn't find an exact match, but here is some related information."*

## 2. API Endpoints

The retrieval pipeline exposes the following Django REST Framework views. 

*(Note: The `RetrievalPipeline` is intentionally initialized globally inside `api/views.py` so the `rank_bm25` index is not unnecessarily loaded from the disk on every single POST request).*

### `POST /api/retrieval/query/`
The standard endpoint. Accepts `query` and an optional `project_id`. 
Returns a cleansed, minimal payload consisting only of the exact chunk content and metadata required for RAG Generation.

### `POST /api/retrieval/query/debug/`
Returns the exact same thing as the standard endpoint, but includes full debugging metadata:
- `stages_completed`: A list showing if the pipeline hit the `cohere_reranking` or skipped it, and if it fell back to `fallback_loose_search`.
- `filter_used`: Shows exactly what `llama-3.1` extracted from the user's natural language query.
- `processing_ms`: Milliseconds taken to execute all 6 stages.

### `GET /api/retrieval/health/`
Used by Kubernetes or Docker to check readiness. 
Checks `dense_svc.client.get_collections()` to ensure Qdrant is alive, and `sparse_svc._index` to ensure BM25 is loaded.

## 3. The Testing Strategy

The Phase 7 testing suite (`document_retrieval/tests/`) achieves total code coverage without ever making a live API call to Google, Groq, or Cohere.

### Strict Dependency Injection
The `RetrievalPipeline` accepts all 6 of its services via its constructor.
```python
pipeline = RetrievalPipeline(
    self_query_svc=Mock(),
    dense_svc=Mock(),
    # ...
)
```
This allows `test_retrieval_pipeline.py` to completely simulate complex scenarios. 
- **Example**: `test_fallback_triggered_when_crag_rejects_all` explicitly mocks the CRAG service to return `([], True)`. The test then verifies that the pipeline catches this, modifies the Qdrant filter to `doc_type=None`, and successfully executes the secondary fallback search.

### `@patch` Decorator Fix
Because we rely on dynamic imports (e.g., `from langchain_groq import ChatGroq` inside the class constructor rather than at the top of the file), the tests correctly patch the origin libraries (`@patch('langchain_groq.ChatGroq')` and `@patch('cohere.Client')`) to ensure the classes are intercepted globally before instantiation.
