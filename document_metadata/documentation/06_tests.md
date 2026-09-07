# Phase 5: Unit Testing Strategy

The `document_metadata` app relies heavily on precise extraction, ensuring older document revisions are safely retired, and adapting to multi-lingual edge cases. Because of this, it is thoroughly tested with 17 rigorous unit tests covering the core logic without hitting live APIs or databases.

## 1. Metadata Extractor Tests (`test_metadata_extractor.py`)

The extractor logic validates Groq/Ollama parsing and graceful failure handling.
Tests implemented:
- `test_extracts_drawing_number_from_title_block_text`: Validates specific structured data extraction.
- `test_extracts_revision_from_text`: Verifies revision isolation.
- `test_returns_confidence_zero_on_both_failures`: Ensures the pipeline does not stall if the LLMs throw exceptions; defaults to `confidence=0.0`.
- `test_falls_back_to_groq_on_ollama_failure`: Confirms the local Ollama failure gracefully triggers the Groq fallback logic.
- `test_returns_empty_schema_not_raises_on_failure`: Validates the pipeline schema safety net.
- `test_validates_approval_status_rejects_invalid_value`: Tests the Pydantic v2 `@field_validator(mode='before')` rejecting values outside the allowed set.
- `test_validates_discipline_rejects_invalid_value`: Confirms strict discipline enforcement.
- `test_confidence_higher_for_more_fields_found`: Tests the priority-weighted confidence scoring math.
- `test_temperature_zero_on_ollama_client`: Enforces `temperature=0.0` for LLM instantiation to guarantee highly deterministic results.

## 2. Version Chain Manager Tests (`test_version_chain_manager.py`)

The chain manager is responsible for correctly retiring superseded documents to prevent "version blindness".
Tests implemented:
- `test_marks_previous_revision_not_current`: Ensures a found predecessor has `is_current=False`.
- `test_sets_superseded_by_id_on_previous`: Verifies the UUID linking.
- `test_returns_false_when_no_previous_revision`: Ensures clean handling of brand-new documents.
- `test_returns_false_when_no_drawing_number`: Verifies guard rails for non-drawing document types.
- `test_atomic_rollback_on_db_failure`: Simulates DB errors to verify the `transaction.atomic()` integrity isn't broken.

## 3. Language Detector Tests (`test_language_detector.py`)

The detector tests cover multi-lingual routing and fallbacks.
Tests implemented:
- `test_detects_english_text`: Standard case validation.
- `test_detects_hindi_text`: Confirms Indian-context language mapping.
- `test_detects_mixed_english_hindi`: Triggers on the 5-character Unicode threshold.
- `test_returns_unknown_for_text_under_50_chars`: Short text fallback.
- `test_returns_unknown_on_langdetect_exception`: Library crash handling.
- `test_detects_urdu_as_hindi`: Language normalization for regional variations.

## 4. Mocks Strategy

To execute cleanly and instantly without hitting the cloud LLMs or live database, the tests consistently use `unittest.mock.patch` across the board:
- **LLM**: Both `ChatOllama` and `ChatGroq` are mocked completely.
- **Database**: `MetadataRepository` is mocked rather than spinning up a SQLite test database, keeping tests atomic.
- **External Dependencies**: `langdetect.detect` is mocked.
