# Phase 2: Task Orchestration

Due to the massive compute required to process 100+ page construction PDFs, Phase 2 is heavily asynchronous. Celery acts as the backbone, backed by a Redis message broker.

---

## 1. The Entry Point: Signals

Phase 2 is completely isolated from HTTP API views. It only triggers when Phase 1 broadcasts a success event.
In `document_processing/signals.py`, we connect to `classification_completed`. The receiver function immediately fires off `process_document_task.delay()`.

---

## 2. Document Orchestrator (`process_document.py`)

This task is responsible for setup and teardown:
1. Validates the document in the `ProcessingRepository`.
2. Marks the job as `SPLITTING`.
3. Opens the PDF via PyMuPDF (`fitz`) simply to count the total number of pages.
4. Updates `total_pages` on the `ProcessingJob` model.
5. **The Map-Reduce Pattern**: It loops through the page count and creates a list of sub-tasks. Using `celery.chord`, it dispatches all page processing tasks to worker queues in parallel.
6. The `chord` defines a callback: `aggregate_results_task`, which will only fire once every single page task in the list has finished.

---

## 3. Page Level Processing (`process_page.py`)

This is where the heavy lifting occurs. By processing at the page level, we gain immense resiliency:
- If Page 44 fails due to a network timeout to the Gemini API, only Page 44 retries. The other 99 pages continue unhindered.
- The task is decorated with `@shared_task(bind=True, max_retries=3, default_retry_delay=30)`.
- **Dynamic Refinement Routing**: Instead of hardcoding post-processing cleaners into the task, it invokes the `RefinementRouter`. Based on the OCR strategy and quality, it sets the `refinement_level` and array of `layers_to_run`. If quality is abysmal, it sets the page status to `NEEDS_REVIEW` and safely halts execution to avoid polluting downstream pipelines.
- **Exponential Backoff**: When an exception is caught (e.g., API timeout), the task raises `self.retry(exc=exc, countdown=retry_delay)`. The delay doubles on every attempt (30s -> 60s -> 120s).
- **Atomic Operations**: When a page finishes, it updates the parent `ProcessingJob.processed_pages` counter using a database-level atomic `F()` expression to prevent race conditions across parallel workers.

---

## 4. Fallback Handling (`retry_failed_page.py`)

If a page fails all 3 of its standard retries, its status is marked as `FAILED`. 
We provide a manual escalation task: `retry_failed_page_task`.
When triggered (usually via an admin API endpoint), this task bypasses the standard `OCRRouter`. It assumes the page is too difficult for standard engines and forces the extraction to run exclusively through the highest-tier LLM (`GEMINI_VISION`).

---

## 5. Recent Stabilizations & Fixes

During End-to-End testing, several critical infrastructure bugs were identified and fixed to stabilize the orchestration layer:

1. **Celery Task Registration**: Fixed `KeyError` and `NotRegistered` errors by properly declaring task modules inside `document_processing/tasks/__init__.py`, ensuring the Celery worker discovers them on startup.
2. **Signal Bridging**: Discovered that Phase 3 (Refinement) was hanging indefinitely because Phase 2 never fired a completion event. Fixed by defining and emitting a custom `processing_completed` Django signal at the end of the `aggregate_results_task`.
3. **Dynamic Pathing**: Resolved `IndexError: page 0 not in document` crashes by replacing strict file path concatenations with the dynamic `Document.storage_path`, ensuring PyMuPDF could actually locate the PDFs regardless of working directory.
4. **Duplicate Task Collisions**: Cleaned up an accidental duplicate definition of `aggregate_results_task` which was causing ambiguous routing within the Celery broker.
