# Phase 4: Chunking Strategies Overview

To ensure the highest quality retrieval during the RAG process, Phase 4 avoids blindly cutting text into equal-sized blocks. Instead, it uses semantic strategies tailored to the structural logic of the specific construction document.

Below is an overview of how the key strategies process text:

## 1. BOQ Chunking (`boq`)
**Goal:** Prevent table rows from being split across multiple chunks, which destroys pricing context.
**Logic:**
- Scans `Phase 2` extracted JSON tables for `Item No`, `Description`, `Qty`, and `Rate` columns.
- Formats each row into a self-contained text block: `"Item 1.1: Concrete Footing | Qty: 50m3 | Rate: $100"`.
- Appends the project context and hierarchy to each chunk.

## 2. Contract Chunking (`contract`)
**Goal:** Isolate specific legal clauses so the LLM can retrieve exact contractual obligations.
**Logic:**
- Uses regex patterns like `(?:^|\n)(?:Clause\s+)?(\d+\.\d+(?:\.\d+)?)\s+([A-Z][^\n]+)` to find headings like "Clause 14.3 - Application for Payment".
- Extracts everything under that heading until the next clause begins.
- Never splits clauses regardless of length, as splitting legally binding clauses is dangerous. If a clause exceeds 3000 characters, it emits a warning log but keeps the clause intact.

## 3. RFI Chunking (`rfi`)
**Goal:** Capture the exact Question and Answer pairs exchanged between contractors and architects.
**Logic:**
- Uses multiline regex `(?s)` to scan for markers like `Question:`, `Query:`, `Response:`, and `Answer:`.
- Creates a single chunk containing the full context: `"RFI Question: [text] \n Architect Response: [text]"`.

## 4. Specification Chunking (`specification`)
**Goal:** Group technical specifications by standard division sections.
**Logic:**
- Identifies main specification headings using standard formatting (e.g., `SECTION 03300 - CAST-IN-PLACE CONCRETE`).
- Recursively splits large specification blocks into sub-chunks maintaining the parent section reference.

## 5. Drawing Chunking (`drawing`)
**Goal:** Convert CAD/PDF drawing metadata and annotations into searchable text.
**Logic:**
- Extracts fields from the Phase 2 `extracted_data` (Titleblock info, Dimensions, Materials, Floor Levels).
- Synthesizes a detailed textual summary of the drawing for pure semantic search.

## 6. Site Log Chunking (`site_log`)
**Goal:** Make daily site logs, weather patterns, and manpower records independently retrievable.
**Logic:**
- Segments pages by `Date` and strips out specific sub-blocks like `Weather`, `Temperature`, `Manpower`, `Activities`, and `Issues`.

## 7. Email Chunking (`email`)
**Goal:** Retain thread context across construction correspondence.
**Logic:**
- Splits text by email headers (`From:`, `Date:`, `Subject:`).
- Normalizes subjects (stripping `Re:`, `Fwd:`) to link chunks via a common `thread_id`.

## 8. Inspection Chunking (`inspection`)
**Goal:** Track QA/QC checklist items and failure remarks.
**Logic:**
- Parses items matching specific `[YES|NO|PASS|FAIL]` patterns.
- Attaches the global inspection date and inspector name to each item-level chunk.

## 9. Engineering Calc Chunking (`calc`)
**Goal:** Preserve calculation blocks and standard references.
**Logic:**
- Splits document based on calculation headers (e.g., `Calculation:`, `Design of:`).
- Extracts referenced standards (e.g., Eurocode, ACI) and ties them to the calculation block.

## 10. Generic Chunking (`generic`)
**Goal:** Safely process unknown or poorly formatted documents without losing data.
**Logic:**
- Utilizes `RecursiveCharacterTextSplitter` from `langchain-text-splitters`.
- Splits text into blocks of exactly 1000 characters.
- Maintains a 200-character overlap between chunks to ensure no sentences or context bridges are lost at the boundary lines.
- **Note:** All specialized strategies fall back to this strategy if their strict regex patterns fail to match.
