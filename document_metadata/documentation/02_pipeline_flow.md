# Phase 5: End-to-End Pipeline Flow

This document explains exactly how a file transitions from Phase 4 (Chunking) into Phase 5 (Metadata Extraction) and how the data is handled.

## 1. The Trigger (Chunking Completed)

When Phase 4 finishes generating chunks for a document, it emits a Django signal: `chunking_completed`. 

The `document_metadata` app listens for this signal in its `apps.py`. The signal receiver instantly triggers the Celery worker: `extract_metadata_task.delay(document_id)`.

## 2. Data Gathering (The Repository)

Once the task starts, the orchestrator asks the `MetadataRepository` for the document's context.

Since Phase 5 is forbidden from importing ORM models from Phase 1, 2, 3, or 4, the repository uses **Raw SQL Queries** to gather the necessary data:
- **Phase 1 Data**: Fetches `doc_type`, `project_id`, and `filename` from `document_classification_document`.
- **Phase 3 Data**: Concatenates all refined pages in correct sequential order from `document_refinement_refinedcontent` into a single text block.

## 3. The Extraction Process

1. **Language Detection**: The text is passed to the `LanguageDetector` to determine if it is English, Hindi, Mixed, or Unknown.
2. **LLM Extraction**: The `MetadataExtractor` truncates the text to the first 3000 characters and sends it to Groq (`llama-3.1-8b-instant`) with a temperature of `0.0` for highly factual, hallucination-free extraction.
3. **Pydantic Validation**: Groq returns structured JSON. The `ExtractedMetadata` Pydantic schema strictly validates the values, ensuring that enums like `approval_status` are restricted to exact values (e.g., `IFC`, `Superseded`).

## 4. Version Chain & Persistence

1. **Atomic Transaction**: The following steps are strictly wrapped in a `transaction.atomic()` block. If any step fails (e.g., chunk backfill fails), the entire database commit is rolled back. This guarantees no orphaned superseded records are left behind during a Celery retry.
2. **Version Update**: The `VersionChainManager` checks if the newly extracted metadata contains a `drawing_number` and `project_id`. If so, it looks for an older revision of that drawing and marks it as `is_current=False` (superseded).
   - **`is_current` Override Logic**: The Celery task then overrides the LLM's `is_current` boolean using a strict 3-step hierarchy: 
     1. If `approval_status == 'Superseded'`, it forces `is_current = False`.
     2. Else, if the LLM successfully extracted an `is_current` boolean, it uses that.
     3. Else, it defaults to `is_current = True`.
3. **Database Save**: The extracted metadata is saved to the local `DocumentMetadata` table using an ORM `update_or_create` call (to ensure idempotency in case of Celery retries).
4. **Chunk Backfill**: The `MetadataRepository` fires a raw SQL query back to Phase 4's `document_chunk` table to bulk-update `is_current` on all the chunks belonging to this document.

## 5. Completion

Once the database transaction is safely committed, Phase 5 emits the `metadata_extracted` signal. This notifies Phase 6 (Vector Indexing) that the document's metadata is ready to be embedded alongside its chunks. Even if Groq fails entirely, the signal is still emitted (with a `confidence=0.0`) to ensure the document pipeline doesn't stall.
