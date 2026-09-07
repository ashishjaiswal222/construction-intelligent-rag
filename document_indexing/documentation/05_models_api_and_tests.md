# Models, API, and Tests

## 1. Database Model
The `IndexingRecord` model stores the operational state of a document's indexing run.
- Tracks `status` (pending, completed, failed).
- Stores integer counts for `chunks_indexed` and `rate_limit_waits`.
- Useful for auditing the AI pipeline.

## 2. API Endpoints
Endpoints are provided strictly for backend observability.
- **GET `/api/indexing/stats/`**: Returns a JSON representation of Qdrant collection size.
- **GET `/api/indexing/health/`**: Returns degraded or ok based on Qdrant and BM25 local status.
- **POST `/api/indexing/reindex/{document_id}/`**: Manually fires the Celery worker for a single document.

## 3. Unit Tests
There are 25 unit tests defined in `document_indexing/tests/`.
The tests execute entirely locally using `unittest.mock.patch` to prevent API network calls to Gemini or creating actual Qdrant local files. They ensure:
1. Pydantic validation handles bad data (e.g., missing type).
2. Qdrant correctly removes None/null values which crash the C++ vector algorithms.
3. The BM25 algorithm maintains idempotency.
4. Celery retries properly if Gemini throws a 429 rate limit.
