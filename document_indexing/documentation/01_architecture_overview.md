# Phase 6: Vector Indexing — Architecture Overview

## 1. The Core Purpose
Phase 6 bridges the gap between text chunks (from Phase 4) and semantic search (in Phase 7). It converts raw construction document chunks into high-dimensional embeddings and stores them in dual indexes for Hybrid Retrieval:
1. **Qdrant (Dense Index):** Stores 768-dimensional semantic vectors for conceptual search ("find something related to...").
2. **BM25 (Sparse Index):** Stores keyword frequency algorithms for exact match retrieval ("find this specific part number...").

## 2. Full Flow After Phase 5
Once Phase 5 successfully extracts metadata, it broadcasts a `metadata_extracted` Django signal.
1. **Signal Received:** Phase 6 catches the signal.
2. **Task Enqueued:** It dispatches `embed_and_index_task` to the Celery worker queue, allowing the HTTP request to return immediately to the user.
3. **Chunk Retrieval:** The worker fetches all chunks for the document via `IndexingRepository` (raw SQL to decouple apps).
4. **Text Preprocessing:** The `TextPreprocessor` expands construction acronyms (e.g., `RFI` → `Request for Information RFI`), normalizes units (`m3` → `cubic metres m3`), and injects context (e.g., `"Construction drawing: ..."`).
5. **Embedding Generation:** The `EmbeddingService` converts the text into 768-D vectors using Gemini's `text-embedding-004` model. It handles batching (100 at a time) and rate limiting (exponential backoff for 429s).
6. **Dual Indexing (Atomicity):**
    - **Qdrant**: Chunks, metadata, and embeddings are upserted.
    - **BM25**: Chunks are added to the in-memory/persisted sparse index.
7. **Completion:** The `IndexingRecord` database table is updated, and an `indexing_completed` signal is fired.

## 3. Storage and Metadata Payload
The data is persisted in:
- `Qdrant` locally at `./construction_qdrant_db/`
- `BM25` locally at `./construction_bm25_index.pkl`

Every chunk stored in Qdrant contains rich **metadata** (35+ fields derived from Phase 5), including `doc_type`, `project_name`, `revision`, `drawing_number`, and `is_current`. This allows Phase 7 to perform "Pre-filtered Vector Search" (e.g., "Semantic search over ONLY current drawings for Project X").
