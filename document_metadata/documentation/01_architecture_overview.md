# Phase 5: Metadata Extraction Architecture Overview

The `document_metadata` application represents Phase 5 of the Construction Intelligence Platform. Its primary responsibility is to extract 35 structured data fields from the text generated in earlier phases using an LLM. This metadata powers the critical retrieval filters in Phase 7, dramatically reducing hallucinations by constraining the search space.

## 1. Clean Architecture Compliance

Phase 5 strictly adheres to the platform's Clean Architecture guidelines, ensuring complete decoupling from previous phases (Phase 1-4).

- **Signals Layer (`signals.py`)**: Entry point for the application. Listens for the `chunking_completed` signal from Phase 4 and triggers the main Celery task.
- **Task Layer (`tasks/`)**: Contains `extract_metadata_task.py`. This task acts as an orchestrator. It manages the timeline, wraps the transaction, and handles exponential backoff retries using the exact formula `60 * (2 ^ retries)` (i.e. 60s -> 120s -> 240s). Absolutely no business logic lives here.
- **Service Layer (`services/`)**: Contains the core logic. 
  - `MetadataExtractor`: Interacts with the Groq LLM to pull structured fields out of the text.
  - `VersionChainManager`: Manages the superseding logic for document revisions.
  - `LanguageDetector`: Determines the language of the document to aid multilingual indexing.
- **Repository Layer (`repositories/`)**: The `MetadataRepository` handles all database interactions. Cross-app data (fetching Phase 1 context, Phase 3 text, and Phase 4 chunk updates) is executed via **raw SQL queries**, completely avoiding cross-app ORM imports.
- **Models & Schemas**: Django model `DocumentMetadata` handles persistence, while Pydantic v2 schema `ExtractedMetadata` enforces strict type validation with `ConfigDict(extra='forbid')`.

## 2. Core Value Proposition

Without Phase 5, the Vector Database (Phase 6) would contain 200,000 unindexed chunks. A query would hit every single one, leading to hallucinations as the AI struggles to figure out which revision of a drawing or which project is being discussed.

By extracting metadata (Project ID, Document Type, Revision, Is Current), Phase 5 allows Phase 7 to filter the query space down to a few thousand chunks. For example, filtering by `is_current=True` immediately eliminates 40-60% of hallucinations.

## 3. Strict Decoupling Rules Enforced

- ❌ No business logic in Celery tasks.
- ❌ No direct Django ORM queries to previous phases (`document_classification`, `document_processing`, `document_refinement`, `document_chunking`).
- ❌ No exceptions raised from the `MetadataExtractor`; it gracefully fails with a confidence score of `0.0`.
- ✅ All cross-boundary data is fetched via raw SQL.
- ✅ The pipeline is guaranteed to continue to Phase 6 even if extraction fails.
