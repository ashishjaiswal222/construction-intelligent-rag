# Phase 5: LLM Extraction Logic

The core extraction logic resides in the `MetadataExtractor` service. It uses `ChatGroq` to interact with the fast `llama-3.1-8b-instant` model.

## 1. Prompt Engineering

The extraction prompt (`METADATA_EXTRACTION_PROMPT`) is highly constrained to prevent the LLM from hallucinating.

**Key Constraints:**
- **Zero-Inference:** The LLM is instructed to *never guess*. It must only extract information explicitly stated in the document text.
- **Null Fallbacks:** If a field is not found, the LLM must return `null` instead of guessing.
- **Strict Enums:** The prompt defines exact allowed values for fields like `approval_status` (IFC, IFR, IFT, Superseded, Approved, Draft, Pending) and `discipline` (structural, architectural, electrical, mechanical, hvac, plumbing, civil).

## 2. Text Truncation

Construction documents can be hundreds of pages long, but metadata (title block, revisions, signatures) is almost exclusively found at the beginning of the document.
To save tokens, increase speed, and avoid context window limits, the extractor only passes the **first 3000 characters** of the concatenated document text to the LLM.

## 3. Pydantic Validation

The LLM is constrained to output structured JSON using Langchain's `with_structured_output(ExtractedMetadata)` feature.

The `ExtractedMetadata` schema acts as a strict secondary safety net. 
- It uses Pydantic v2's `model_config = ConfigDict(extra='forbid')` to reject any hallucinated fields not explicitly defined in the schema.
- It uses Pydantic v2's `@field_validator('approval_status', mode='before')` combined with `@classmethod` to catch any instances where the LLM disobeys the enum constraints before parsing completes. If the LLM returns an invalid `approval_status`, the validator silently converts it to `None` rather than crashing the pipeline.

## 4. Priority-Weighted Confidence Scoring

Not all metadata fields are equally important. For a drawing, the `drawing_number` is critical. For an RFI, the `author` is critical. 

The application maps `DOC_TYPE_PRIORITY_FIELDS` for each document type. 
The confidence score is dynamically calculated based on how many *priority* fields were successfully extracted, rather than just doing a raw count of all 35 possible fields.

For example, if a drawing has 5 priority fields, and Groq finds 4 of them, the confidence score is `0.8` (80%), even if it missed 20 other irrelevant fields like `wbs_code`.
