# Phase 3: Architecture and Flow

## Overview
Phase 3 represents the **OCR Refinement Layer** of the Construction Intelligence Platform. It acts as a specialized post-processing engine that takes the raw text extracted during Phase 2 and applies highly targeted, strategy-aware cleaning layers.

The primary design philosophy of Phase 3 is **Total Decoupling**. It is built as a completely separate Django application (`document_refinement`) that functions independently of the core OCR engine.

---

## High-Level Architecture

The `document_refinement` application adheres to a strict decoupling pattern:

1. **Signals**: The entry point. Listens for the `processing_completed` signal broadcast by Phase 2.
2. **Tasks (Celery)**: Uses a map-reduce chord pattern to refine all pages of a document in parallel.
3. **Orchestrator**: The `RefinementOrchestrator` governs the pipeline. It reads the requested `layers_to_run` for a page and selectively triggers the appropriate refinement logic.
4. **Layers (Services)**: Five distinct service classes, each responsible for a highly specialized type of text correction (e.g., Structural Repair, Semantic Validation).
5. **Repositories**: The exclusive data access layer. Because Phase 3 is forbidden from importing Phase 2 models, it uses Raw SQL (`JOIN` queries) to fetch the necessary Phase 2 data.
6. **Models & Schemas**: Strictly defined data contracts ensuring the `raw_text` is preserved and all quality metrics are meticulously tracked.

---

## Execution Flow: Step-by-Step

### 1. Triggering the Pipeline
When Phase 2 successfully finishes extracting text for an entire document, its aggregate task emits a `processing_completed(document_id)` signal. The receiver in `document_refinement/signals.py` catches this and immediately dispatches the `refine_document_task` to the Celery queue.

### 2. Document-Level Orchestration
The `refine_document_task` initiates the refinement process:
- It queries the `RefinementRepository` for all `COMPLETED` pages in the given document that require refinement (where `refinement_level != 'NONE'`).
- It generates a Celery `chord`, dispatching a parallel `refine_page_task` for **every single page**.

### 3. Page-Level Refinement
Each `refine_page_task` runs independently:
- The task loads the `raw_text`, `doc_type`, `refinement_level`, and `layers_to_run` via raw SQL.
- It instantiates the `RefinementOrchestrator` and the 5 refinement layers.
- The Orchestrator calculates the baseline text quality (`quality_before`).
- The Orchestrator strictly executes **only** the layers explicitly listed in the `layers_to_run` array. (e.g., a perfect digital text layer might skip spell-checking but undergo structural repair).
- The Orchestrator calculates the final text quality (`quality_after`).
- If the final quality is poor (< 0.65), the orchestrator automatically flags the page with `needs_human_review = True`.

### 4. Storage and Aggregation
The Orchestrator returns a strict `RefinementResult` Pydantic object. The task uses the `RefinementRepository` to save this payload into the `RefinedContent` PostgreSQL table.

Once all parallel page tasks finish, the Celery chord triggers the `refinement_aggregate_task`, which logs completion and broadcasts the final `refinement_completed` signal (alerting downstream ERP systems or future pipelines).
