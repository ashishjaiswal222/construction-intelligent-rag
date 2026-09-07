# Phase 6: Pipeline Flow

## The Step-by-Step Flow

When the `metadata_extracted` signal fires from Phase 5, the following asynchronous process kicks off in the background:

1. **Signal Catch**: The `apps.py` registry catches the signal and hands it to `embed_and_index_task.delay(document_id)`.
2. **Task Initialization**: The Celery worker initializes the task and checks for any prior versions of the document.
3. **Database Fetching**: `IndexingRepository` connects to `document_chunking_documentchunk` and `document_metadata` to retrieve raw data and metadata, combining them.
4. **Idempotent Cleanup**: If this is a document update (re-run), the task instructs `QdrantIndexService` and `BM25IndexService` to delete any old chunks for this `document_id`.
5. **Preprocessing**: The raw text is passed to `TextPreprocessor` for abbreviation and unit normalisation.
6. **Embedding Generation**: The preprocessed text is grouped into batches of 100 and sent to `EmbeddingService` where Gemini creates `768-D` vectors.
7. **Qdrant Indexing**: `QdrantIndexService` upserts the 768-dimensional vectors into the local Qdrant Vector Store along with 35 fields of metadata.
8. **BM25 Indexing**: `BM25IndexService` tokenizes the text and adds the document to the local sparse index.
9. **Finalization**: An `IndexingRecord` is saved to the database (or updated) noting success, time taken, and total chunks indexed. A completion signal `indexing_completed` is fired for downstream systems.

## Failure Resilience
- The pipeline is fault-tolerant. If Qdrant goes down or API rate limits fail, Celery retries the job automatically via exponential backoff.
- The dual-write index process (Qdrant + BM25) is wrapped in an atomic database transaction. If one fails, the pipeline aborts safely.
