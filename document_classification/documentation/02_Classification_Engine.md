# The 3-Layer Classification Engine

The core logic of the system resides in the `ClassifierService` (`document_classification/services/classifier_service.py`). To ensure high accuracy while keeping inference costs low, the classification is split into three distinct layers.

## Layer 1: File Analysis (`FileAnalyzerService`)
Before handing anything over to an LLM, the system performs a deterministic file analysis.
*   **Text Extraction**: It uses `PyMuPDF` (`fitz`) to rapidly extract the first few pages of text from the PDF.
*   **Image Detection**: It checks if the PDF pages contain binary images (`page.get_images()`). This is crucial because if a document is purely an image, we know immediately that we must trigger an OCR strategy rather than relying on standard text parsing.
*   **Result**: Returns a `FileAnalysisResult` containing `mime_type`, `page_count`, `has_images`, and up to 2500 characters of `preview_text`.

## Layer 2: Heuristic Engine (`HeuristicClassifierService`)
Large Language Models are expensive and slow. If a document can be classified using deterministic rules, we bypass the LLM entirely.

### Content-Aware Contradiction Engine
Our heuristic engine is "Content-Aware". It does not blindly trust the filename. It receives both the `filename` and the `preview_text` extracted by Layer 1.
*   **Regex & Keyword Matching**: The engine checks the filename for known structures (e.g., `"RFP"`, `"Site Log"`, `"BOQ"`).
*   **Contradiction Checking**: Before returning a heuristic classification, the engine scans the `preview_text`. If a user uploads a Site Log named `BOQ_Final.pdf`, the engine notices that the document text is missing required BOQ keywords (like `"Amount"`, `"Quantity"`, `"Rate"`).
*   **Fallback**: Upon detecting this contradiction, the Heuristic Engine rejects the document (`returns None`). This safely forces the mislabeled document to fall through to the LLM (Layer 3) for accurate reading, ensuring we never misclassify a file just because it has a bad name.

**Benefit**: This guarantees 100% precision on cleanly named files, requires 0 API tokens, and completely mitigates the risk of users uploading misnamed files.

## Layer 3: LLM Factory (`LLMFactory` & `BaseLLMProvider`)
If the heuristics fail to yield a confident match, the system falls back to the LLM Factory.

### The Structured Output Schema
The system uses **Pydantic** (`DocumentClassification` schema) to force the LLM to return exactly the data types we need.
```python
class DocumentClassification(BaseModel):
    doc_type: str
    confidence: float
    has_tables: bool
    has_images: bool
    language: str
    # ...
```

### Primary vs Fallback LLM Strategy
To optimize for both speed/cost and resilience, we use two LLMs:

1.  **Primary LLM (Groq - LLaMA-3.1-8b)**:
    *   **Why**: Groq uses Language Processing Units (LPUs) which provide incredibly fast inference (~800+ tokens per second) at a fraction of the cost of OpenAI.
    *   **The Problem**: Smaller models (like 8b) occasionally hallucinate when forced into strict JSON structured outputs, sometimes duplicating JSON keys (which causes Pydantic/LangChain `tool_use_failed` parsing errors).
2.  **Fallback LLM (Gemini 2.0 Flash)**:
    *   **How it works**: If the Groq API call throws an `Exception` (due to parsing failure, API outage, or timeout), the `try/except` block in `ClassifierService` automatically catches it and routes the exact same prompt to Gemini.
    *   **Low Confidence Override**: Additionally, if Groq returns a valid JSON but its self-reported `confidence < 0.75`, the system asks Gemini for a second opinion.

### The Prompt Architecture
The `CLASSIFICATION_PROMPT` is designed as an expert system prompt. It provides the LLM with:
*   The system persona ("expert construction document classifier").
*   The exact `doc_type` choices it is allowed to pick from.
*   Guidelines on choosing specific `chunking_strategy` and `ocr_strategy` values so downstream RAG systems know how to parse the document (e.g., `clause_based` for contracts vs. `table_row` for BOQs).
