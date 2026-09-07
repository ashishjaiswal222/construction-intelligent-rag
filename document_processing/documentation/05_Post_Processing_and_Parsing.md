# Phase 2: Post-Processing and Parsing

Raw OCR text is rarely perfect, especially in the construction domain. Phase 2 features a robust post-processing pipeline to clean, format, and structure the data into Pydantic models. 

**Crucially, post-processing is governed by the `RefinementRouter`.** Instead of blindly running all cleaners on every string, the router evaluates the source strategy (e.g., `TEXT_LAYER` requires minimal fixing, while `PADDLE_OCR` requires spelling correction) and dynamically returns a `layers_to_run` array, ensuring targeted and compute-efficient refinement.

---

## 1. Content Cleaning (`content_cleaner.py`)

The `ContentCleaner` runs on every string of text extracted. It utilizes Regular Expressions (`re`) to fix common hallucination patterns:
- **Alphanumeric Confusion**: Fixes instances where a zero "0" is placed before uppercase letters (changes to "O"), or a lowercase "l" is placed between digits (changes to "1").
- **Domain Specific Typos**: Corrects known failures like `concrele` -> `concrete`, `specilication` -> `specification`, and `reinforoced` -> `reinforced`.
- **Measurement Units**: Converts `m2` and `m3` to their proper unicode representations (`m²`, `m³`).

Additionally, it identifies and extracts `[HW: ...]` (Handwriting) and `[STAMP: ...]` tags placed by the LLMs, separating them into distinct arrays for the `OCRPageResult` schema.

---

## 2. Symbol Normalization (`engineering_symbol_normalizer.py`)

Construction documents are packed with engineering symbols that differ wildly based on the OCR engine. The normalizer enforces a strict standard:
- Converts `degrees` or `deg.` into `°`
- Consolidates all variations of phi (`φ`, `⌀`) into the standard capital `Φ` (often used for rebar diameter).
- Maps `+/-` to `±`, and `>=` to `≥`.

---

## 3. Table Extraction (`table_extractor.py`)

If a page is identified as containing tables (e.g., a Bill of Quantities), the `TableExtractor` takes over.
- It bypasses standard text OCR and sends the image directly to Gemini 2.0 Flash.
- **The Prompt**: Uses `TABLE_EXTRACTION_PROMPT` to enforce strict JSON output.
- **Data Integrity**: Crucially, it does *not* flatten the table. It extracts the raw `headers`, `rows`, and a special `merged_cells` dictionary. This ensures that complex spanned rows/columns in pricing tables maintain their mathematical integrity for downstream ERP systems.
- The output is validated against the `TableResult` Pydantic schema before saving to the JSONB database column.

---

## 4. Drawing Understanding (`drawing_understanding_service.py`)

If the document is classified as an Architectural or Engineering Drawing:
- The system focuses entirely on metadata extraction rather than dense text reading.
- It parses the Title Block, extracting the `drawing_number`, `revision`, `discipline` (e.g., Structural, MEP), and `scale`.
- It identifies the `revision_history` grid, parsing out previous dates and approvals.
- It returns a `DrawingResult` Pydantic model. If the LLM hallucinates an invalid JSON structure, the service catches the exception and gracefully returns an empty schema with `null` fields rather than crashing the pipeline.
