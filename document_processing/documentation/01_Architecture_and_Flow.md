# Phase 2: Architecture and Flow

## Overview
Phase 2 represents the **Production OCR, Content Extraction, and Document Parsing Layer** of the Construction Intelligence Platform. It takes over immediately after Phase 1 (Document Classification) has successfully identified and labeled an uploaded document.

This phase is designed to be highly resilient, scalable, and intelligent—dynamically routing pages to the best extraction engine (Text Layer, PaddleOCR, or Gemini Vision) based on heuristic analysis and confidence scoring.

---

## High-Level Architecture

The `document_processing` application strictly adheres to a deeply decoupled, layered architecture:

1. **Signals**: The entry point. Listens for the `classification_completed` signal from Phase 1.
2. **Tasks (Celery)**: Orchestrates the work asynchronously. Handles splitting documents into pages and processing them in parallel.
3. **Services**: Contains pure business logic. Decoupled from Django ORM and Celery.
4. **Repositories**: The exclusive data access layer. Services never run raw ORM queries; they only interface with Repositories.
5. **Models**: Pure Django models representing the database schema (PostgreSQL with JSONB).
6. **Schemas**: Pydantic v2 schemas used for strict data contracts between services.

---

## Execution Flow: Step-by-Step

### 1. Triggering the Pipeline
When Phase 1 successfully classifies a document, it emits a `classification_completed` signal. The receiver in `document_processing/signals.py` catches this and immediately dispatches the `process_document_task` to the Celery queue.

### 2. Document Splitting (Orchestration)
The `process_document_task` acts as the master orchestrator:
- It creates a `ProcessingJob` record in the database with the status `SPLITTING`.
- It uses `PyMuPDF` (`fitz`) to read the PDF and determine the total number of pages.
- It generates a Celery `chord`, dispatching a parallel `process_page_task` for **every single page** in the document.

### 3. Page-Level Processing
Each `process_page_task` runs independently, allowing partial failures and parallel execution:
- **Metadata Extraction**: Analyzes basic heuristics (like checking if the document type is a "drawing" or a "boq").
- **Text Layer Check**: Fast-paths the page if a pristine digital text layer exists.
- **Routing**: The `OCRRouter` decides the optimal extraction strategy (`TEXT_LAYER`, `GEMINI_VISION`, or `PADDLE_OCR`).
- **Extraction**: The chosen engine processes the image/PDF. If PaddleOCR yields low confidence (< 0.78), the `EnsembleService` automatically escalates the page to Gemini Vision.
- **Quality Assessment**: The `OCRQualityService` calculates a confidence score based on alphanumeric ratios and symbol density. Poor quality (< 0.55) triggers an automatic Celery retry with backoff.
- **Parsing & Refinement**: The `RefinementRouter` evaluates the extraction quality and strategy. It dynamically determines the `refinement_level` (NONE, LIGHT, MEDIUM, HEAVY) and precisely which cleaning layers (like `ContentCleaner` or `EngineeringSymbolNormalizer`) to execute, ensuring we don't waste compute on garbage text. Pages with extremely low quality are flagged as `NEEDS_REVIEW` and skip refinement.
- **Structured Extraction**: If tables or drawings are detected, specialized Gemini prompt templates are used to extract heavily structured JSON data.

### 4. Storage and Aggregation
All raw text, cleaned text, and deeply structured JSON objects (tables, drawing metadata) are saved to the PostgreSQL database via the `PageRepository` and `ContentRepository`. The page status is marked as `COMPLETED`.

Once all parallel page tasks finish, the Celery chord triggers the `aggregate_results_task`, which marks the overall `ProcessingJob` as `COMPLETED`.
