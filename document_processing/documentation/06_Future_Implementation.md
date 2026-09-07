# Phase 2 & 3: Future Implementation & Scalability

As the pipeline scales to handle thousands of heavy construction documents concurrently, the following architectural upgrades should be implemented to ensure high availability, zero data loss, and optimal performance.

---

## 1. API Key Rotation Pool (Phase 2 & 3)
**The Problem:** Gemini Vision (Phase 2 fallback) and Groq Llama-3 (Phase 3 refinement) are currently bound to single API keys. Free tier quotas (e.g., `429 Too Many Requests`) will halt pipeline execution.
**The Implementation:**
1. Update `.env` to accept comma-separated keys: `GEMINI_API_KEYS=key1,key2,key3`.
2. Create a `KeyManager` singleton in `shared/services/` that acts as a round-robin load balancer.
3. If an API call receives a `429`, the `KeyManager` automatically marks that key as "cooldown" for 60 seconds and instantly retries the request with the next key in the pool.

## 2. Hardened Celery Retry Strategies (Phase 2)
**The Problem:** Currently, when the `TableExtractor` encounters a `429 Quota Exceeded` error from Gemini, it catches the exception and returns an empty list to prevent crashing the worker. While safe, this results in silent data loss for tables.
**The Implementation:**
1. Define a custom `RateLimitException`.
2. In `table_extractor.py`, raise `RateLimitException` instead of swallowing the error.
3. In `process_page.py`, add a specific `autoretry_for=(RateLimitException,)` configuration to the Celery task with a high exponential backoff (`countdown=60`). This ensures the task pauses and cleanly retries later without dropping table data.

## 3. High-Concurrency Database Pooling (Phase 2)
**The Problem:** When running `--pool=threads --concurrency=100`, 100 simultaneous Celery workers will attempt to open 100 concurrent connections to PostgreSQL to save `OCRResult` and `Page` statuses. This will exhaust the database connection limit (`FATAL: sorry, too many clients already`).
**The Implementation:**
1. Install and configure **PgBouncer** as a middleware connection pooler.
2. In Django's `settings.py`, configure `CONN_MAX_AGE` and ensure `CONN_HEALTH_CHECKS` are enabled to recycle stale connections cleanly across Celery threads.

## 4. Multi-Page Contextual Classification (Phase 1)
**The Problem:** Classification currently relies solely on the first page. If a document has a generic cover page, classification defaults to `unknown`.
**The Implementation:**
1. Update `classify_document_task.py`.
2. Extract text from Page 1, 2, 3, and the final page.
3. Concatenate the text chunks before sending to the LLM. This provides the AI with index structures, headers, and signature blocks to guarantee 99% accurate classification.

## 5. Dynamic Quality Gates (Phase 3)
**The Problem:** The current Refinement Quality Gate strictly fails any output that is `1.3x` longer than the input text (to prevent hallucination). However, a BOQ table full of heavy abbreviations (e.g., "R/F B/W") will naturally expand well beyond 1.3x when passed through the `abbreviation_expander` layer.
**The Implementation:**
1. Refactor `RefinementOrchestrator` to calculate a dynamic Quality Gate multiplier.
2. If `refinement_level == HEAVY` and `layers_applied` includes `abbreviation_expander`, dynamically raise the constraint to `1.5x` or `1.6x` to allow for valid expansions while still catching rogue hallucinations.

## 6. GPU-Accelerated PaddleOCR (Phase 2)
**The Problem:** Local PaddleOCR extraction for scanned blueprints currently relies on CPU execution (`~1.5s` per page).
**The Implementation:**
1. Provision a machine with an NVIDIA GPU and CUDA toolkit installed.
2. Update the Python environment to use `paddlepaddle-gpu`.
3. In `PaddleService`, ensure `use_gpu=True` is explicitly passed. This will drop extraction times to `< 0.1s` per page.

---

## 7. Fine-Grained Region-Based Multi-Engine OCR Pipeline (Phase 2)
**The Problem:** Current OCR routing operates at the **page level**. In complex construction documents, a single page often contains printed text, BOQ tables, handwritten field notes, wet stamps, and CAD title blocks simultaneously. Sending a multi-element page to a single extractor causes data loss for minor elements.
**The Implementation:**
1. Integrated layout segmentation model (`LayoutLMv3` / `YOLOv8-Layout`) in `document_processing/services/layout/`.
2. Segment pages into bounding box crops (`TEXT`, `TABLE`, `HANDWRITING`, `STAMP`, `DRAWING`).
3. Route each crop independently to its specialized engine and reassemble into a `UnifiedStructuredPageRecord`.
4. Full architectural spec saved at: [future_enhancement_docs/multi_region_ocr_pipeline.md](file:///c:/Users/Ashish%20jaiswal/Downloads/generative%20ai/accuracy_construction_Rg/future_enhancement_docs/multi_region_ocr_pipeline.md).

---

## 8. Parallel Fan-Out/Fan-In Celery Chord Orchestration & Large PDF Chunking (Phase 2)
**The Problem:** Processing large 500-page engineering PDFs with individual page tasks can flood the task broker. Additionally, multi-region extractions per page need a deterministic fan-in callback before starting refinement.
**The Implementation:**
1. Dynamic page batching for PDFs > 50 pages (grouping 10 pages per batch).
2. Parallel multi-region region detection and worker execution per page.
3. Deterministic Celery Chord fan-in aggregator (`aggregate_results_task`) to merge page elements into a `Unified Structured Document`.
4. Full architectural spec saved at: [future_enhancement_docs/parallel_fanout_orchestration.md](file:///c:/Users/Ashish%20jaiswal/Downloads/generative%20ai/accuracy_construction_Rg/future_enhancement_docs/parallel_fanout_orchestration.md).
