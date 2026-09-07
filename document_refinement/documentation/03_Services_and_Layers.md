# Phase 3: Services and Layers

The heart of Phase 3 is the `RefinementOrchestrator` and its five specialized cleaning layers. Each layer focuses on a single domain of text repair.

---

## 1. Layer 1: Structural Repair
**Scope**: Layout, formatting, and pagination artifacts.
- Removes orphaned page numbers (`42`) and pagination footers (`Page X of Y`).
- Repairs broken sentences caused by OCR column misreads (merges lines that lack ending punctuation and precede a lowercase letter).
- Repairs hyphenated line breaks (e.g., `hy- \n phenated` -> `hyphenated`).
- Collapses excessive whitespace (3+ blank lines reduced to exactly 2).

## 2. Layer 2: OCR Correction
**Scope**: Character confusion and spelling.
- **Safety**: This layer is explicitly disabled for `TEXT_LAYER` and `GEMINI_VISION` strategies to prevent corrupting perfect text. It runs heavily on `PADDLE_OCR` outputs.
- Fixes structural character confusion (e.g., `0` before uppercase letters becomes `O`, `1` trapped between letters like `Il` becomes `II`).
- Uses regex to correct dozens of common construction domain OCR errors (e.g., `concrele` -> `concrete`, `specilication` -> `specification`).
- Restores proper unit unicode characters (`m3` -> `m³`).

## 3. Layer 3: Symbol Normalizer
**Scope**: Engineering symbols and grade expansions.
- Standardizes messy diameter notations (`φ`, `⌀`, `∅`) to the standard `Ø`.
- Standardizes `deg.` or `degrees` to `°`.
- Standardizes math operators (`+/-` to `±`, `>=` to `≥`).
- Expands short-hand material grades into highly searchable, explicit strings (e.g., `C35` -> `Grade C35 (35 N/mm² concrete)`, `Fe500` -> `Grade Fe500 rebar (500 N/mm²)`).

## 4. Layer 4: Abbreviation Expander
**Scope**: Domain abbreviations (without destroying codes).
- Uses complex negative lookahead regex to expand common abbreviations while keeping the original acronym in brackets.
- Example: `RFI` becomes `Request for Information (RFI)`. This ensures downstream vector databases match on both the acronym and the full definition.
- **Protection**: The negative lookahead (`(?![-\/]\d)`) ensures that document codes are ignored. So while `RFI` expands, an identifier like `RFI-023` remains perfectly intact as `RFI-023`.

## 5. Layer 5: Semantic Validator
**Scope**: AI-driven context repair for garbage text.
- **Cost Protection Gate**: This layer uses LLM compute (`groq` API). Therefore, it features an extremely strict `should_run()` gate. It only executes if:
  - The page is routed for `HEAVY` refinement.
  - The quality score is *still* terrible (< 0.75) even after Layers 1-4.
  - It is a dense document type (Contract, BOQ, Specification, Drawing).
  - It has not been retried before (to prevent infinite LLM loops).
- **Hallucination Protection**: It sends a snippet to the Llama 3 model. If the model hallucinates and returns text that is > 1.3x the length of the original snippet, the orchestrator instantly rejects the repair and falls back to the Layer 4 output.
