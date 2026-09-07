# Phase 3: Database and Schemas

To maintain architectural independence, Phase 3 implements its own database tables and schemas, enforcing a rigid boundary between the raw OCR extraction and the refined content.

---

## Pydantic Data Contracts (Schemas)

All data flowing out of the Refinement Orchestrator must conform to the `RefinementResult` schema.

### `RefinementResult`
Defined with `model_config = ConfigDict(extra='forbid')` to ensure strict typing.
- **Identity**: `page_id` (UUID).
- **Text Payloads**: `raw_text` (the untouched original), `cleaned_text` (the final result).
- **Metrics**: `quality_before`, `quality_after`, `quality_delta`, `char_count_before`, `char_count_after`, `processing_ms`.
- **State**: `refinement_level`, `layers_applied` (array of what actually ran).
- **Flags**: `passed_quality_gate`, `needs_human_review`, `semantic_validation_used`, and `refinement_flags` (array of issues like `multiple_unclear_segments`).

---

## Django ORM Models

### `RefinedContent`
This is the single table utilized by Phase 3, mapped to the PostgreSQL database.
- **Crucial Decoupling**: The `page_id` is stored as a standard `UUIDField` with a database index, **NOT** as a Django `ForeignKey` to Phase 2's `Page` model. This ensures Phase 3 can operate without importing Phase 2 models, preventing tightly-coupled codebases.
- **Data Preservation**: It stores both the `raw_text` and `cleaned_text`. This guarantees that if a refinement layer hallucinates or corrupts the data, the original OCR payload is always safe and recoverable.
- **Indexes**: `page_id`, `needs_human_review`, and `passed_quality_gate` are heavily indexed for lightning-fast API queries (e.g., loading the human review queue).

---

## The Repository Pattern

The `RefinementRepository` handles all data access.

### Raw SQL Joins
Because `document_refinement` cannot import models from `document_processing`, the repository utilizes `django.db.connection.cursor()` to execute Raw SQL queries. 

For example, `get_pages_for_document(document_id)` runs a complex `JOIN` across `document_processing_page`, `document_processing_ocrresult`, `document_processing_processingjob`, and `document_classification_document` to fetch all necessary context (`raw_text`, `doc_type`, `layers_to_run`) without violating the dependency rules.
