# Phase 3: Task Orchestration

Task orchestration in Phase 3 is designed to mirror the highly successful Map-Reduce pattern utilized in Phase 2, ensuring that scaling up to a 1,000-page document remains fast and fault-tolerant.

---

## The Celery Map-Reduce Pipeline

### 1. `refine_document_task` (The Mapper)
This task is fired automatically via the `processing_completed` signal.
- It queries the `RefinementRepository` for every page belonging to the document.
- It maps these pages into an array of Celery task signatures: `[refine_page_task.s(page_1), refine_page_task.s(page_2), ...]`.
- It executes these tasks using `celery.chord`, which instructs the Redis broker to process them in parallel across all available worker nodes.

### 2. `refine_page_task` (The Worker)
This is the isolated worker task.
- It tracks execution time (`processing_ms`).
- It passes the raw data into the `RefinementOrchestrator` which runs the cleaning layers inside a safe `try/except` block.
- It saves the `RefinedContent` to the database.
- If the final calculated quality is below 65% (`quality_after < 0.65`), it does NOT crash or raise an exception. It simply flags the payload with `needs_human_review = True` and completes successfully. This ensures one garbage page doesn't halt the entire document.

### 3. `refinement_aggregate_task` (The Reducer)
This is the chord callback.
- It is physically impossible for this task to fire until every single `refine_page_task` in the array has returned successfully or exhausted its retries.
- Once fired, it emits the final `refinement_completed` Django signal.

---

## Resilience and Safety

- **No Business Logic in Tasks**: Tasks handle only I/O (Database reads/writes) and Celery state. All complex text manipulation lives inside the `services/` directory.
- **Fail-Safe Orchestrator**: The `RefinementOrchestrator` traps all exceptions. If an aggressive Regex pattern in Layer 2 throws an error, or the Groq API in Layer 5 crashes, the Orchestrator swallows the exception, appends a `refinement_failed` flag, and returns the raw text untouched.
- **Exponential Backoff**: If the database is locked or Redis stutters, the Celery tasks will retry with exponential backoff (`default_retry_delay=30`).
