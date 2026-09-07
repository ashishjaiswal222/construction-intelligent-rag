# Phase 4: Intelligent Chunking Architecture Overview

The `document_chunking` application represents Phase 4 of the Construction Intelligence Platform. Its primary responsibility is to take refined, high-quality text and structured data (from Phase 3) and convert it into semantic, retrievable chunks optimized for Vector Database indexing and RAG (Retrieval-Augmented Generation).

## 1. Clean Architecture Compliance

Phase 4 strictly adheres to the platform's Clean Architecture guidelines to ensure zero tight coupling with previous phases.

- **Signals Layer (`signals.py`)**: Entry point for the application. Listens for the `refinement_completed` signal from Phase 3.
- **Task Layer (`tasks/`)**: Celery tasks (`chunking_aggregate_task.py` and `chunk_document_task.py`) handle async orchestration, parallelization, and error backoff. Absolutely no business logic lives here.
- **Service Layer (`services/`)**: Contains the core business logic. The `ChunkingService` orchestrates the chunking process, while the `ChunkingStrategyDispatcher` routes documents to their specific strategy implementations.
- **Repository Layer (`repositories/`)**: The `ChunkingRepository` handles all database interactions. Cross-app data (fetching Phase 1 metadata, Phase 2 tables, Phase 3 refined text) is executed via **raw SQL queries**, completely avoiding cross-app ORM imports.
- **Models & Schemas**: Django models (`ChunkingJob`, `DocumentChunk`) handle persistence, while Pydantic v2 schemas (`ChunkResult`) enforce strict type validation with `ConfigDict(extra='forbid')`.

## 2. Parallel Processing Strategy

Because construction documents can be hundreds of pages long, chunking cannot be executed synchronously in a single thread without risking timeouts.

Phase 4 uses a **Celery Map-Reduce Pattern**:
1. When a document finishes refinement, the `chunk_document_task` orchestrator is triggered.
2. It generates a single `ChunkingJob` tracker.
3. Instead of processing the entire document sequentially, it utilizes the strategy dispatcher to process the document (which queries all completed pages for that document in one go, or can be chunked per-page depending on the strategy).
4. The parallelization is designed to scale horizontally across Celery workers, tracking progress via atomic database updates on the `ChunkingJob` model.

## 3. Strict Decoupling Rules Enforced
- ❌ No business logic in Celery tasks.
- ❌ No direct Django ORM queries to `document_classification`, `document_processing`, or `document_refinement` models.
- ❌ No `RecursiveCharacterTextSplitter` used for named/structured document types.
- ✅ All cross-boundary data is passed via signal `kwargs` or fetched via raw SQL.
