# Phase 4: End-to-End Pipeline Flow

This document explains exactly how a file transitions from Phase 3 (Refinement) into Phase 4 (Chunking) and how the data is handled.

## 1. The Trigger (Refinement Completed)
When Phase 3 finishes refining a document's OCR text, it emits a Django signal: `refinement_completed`. 

The `document_chunking` app listens for this signal in its `apps.py` (which loads `signals.py`). The signal receiver instantly triggers the Celery worker: `chunk_document_task.delay(document_id)`.

## 2. Data Gathering (The Repository)
Once the task starts, the `ChunkingService` asks the `ChunkingRepository` for the document's context.

Since Phase 4 is forbidden from importing ORM models from Phase 1, 2, or 3, the repository uses **Raw SQL Queries** to gather the necessary data:
- **Phase 1 Data**: Fetches `doc_type`, `project_id`, and `filename` from `document_records`.
- **Phase 2 Data**: Fetches raw extracted JSON tables and drawings from `document_processing_extractedcontent`.
- **Phase 3 Data**: Fetches the highly accurate, semantically corrected text (`cleaned_text`) from `refined_content`.

## 3. The Chunking Process
1. **Job Creation**: A `ChunkingJob` is created in the database to track progress.
2. **Strategy Dispatch**: The service looks at the `doc_type` (e.g., `boq`, `contract`, `rfi`) and asks the `ChunkingStrategyDispatcher` for the correct chunking logic.
3. **Execution**: The specialized strategy iterates through the refined pages. It uses regular expressions, structural markers, and Langchain's advanced splitters to cut the text into semantic chunks.
4. **Persistence**: The resulting chunks are validated through a strict Pydantic `ChunkResult` schema and then bulk-inserted into the `document_chunk` table.

## 4. Completion
Once all pages are chunked, the parallel tasks converge at the `chunking_aggregate_task`.
This task:
1. Counts the total number of chunks created.
2. Builds a JSON breakdown of which strategies produced how many chunks.
3. Evaluates the success rate to determine the final status (`COMPLETED` if no failures, `PARTIAL` if some pages failed but others succeeded, or `FAILED` if no chunks were generated).
4. Records the completion time and fires the `chunking_completed` signal, which notifies Phase 5 (Indexing) that the document is ready to be embedded into the Vector Database.
