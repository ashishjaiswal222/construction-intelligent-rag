# Phase 4: Strategy Routing Logic

Documents in the construction industry are highly varied. A Bill of Quantities (BOQ) requires completely different chunking logic than a legal FIDIC Contract.

Phase 4 solves this using a **Strategy Pattern** managed by the `ChunkingStrategyDispatcher`.

## The Dispatcher Mechanism

The `ChunkingStrategyDispatcher` is a factory class located in `services/dispatcher.py`. 

When the `ChunkingService` receives a document, it queries Phase 1 for the `doc_type`. It then passes this `doc_type` to the dispatcher:

```python
strategy = ChunkingStrategyDispatcher.get_strategy(doc_type)
chunks = strategy.chunk_document(document_id, pages_data, tables_data, context)
```

### Route Mapping
The dispatcher contains a hardcoded registry mapping `doc_type` strings to their respective Python classes:

- `'contract'` ➔ `ContractChunkingStrategy`
- `'boq'` ➔ `BOQChunkingStrategy`
- `'rfi'` ➔ `RFIChunkingStrategy`
- `'specification'` ➔ `SpecificationChunkingStrategy`
- `'drawing'` ➔ `DrawingChunkingStrategy`
- `'site_log'` ➔ `SiteLogChunkingStrategy`
- `'email'` ➔ `EmailChunkingStrategy`
- `'inspection'` ➔ `InspectionChunkingStrategy`
- `'calc'` ➔ `EngineeringCalcChunkingStrategy`
- *Any unknown type* ➔ `GenericChunkingStrategy`

## The Fallback Safety Mechanism
Construction documents are messy. Even if a document is classified as an `rfi`, it might be an empty template, or the OCR might have failed to read the specific "Question:" / "Answer:" headers.

To prevent the pipeline from crashing or dropping data, **every specialized strategy implements a fallback safety net**.

If a specialized strategy runs, but yields `0` chunks (meaning its strict regex patterns failed to find a match), it automatically instantiates the `GenericChunkingStrategy`. The Generic strategy splits the text using robust, overlapping character windows (e.g., Langchain's `RecursiveCharacterTextSplitter`), ensuring the text is still indexed and retrievable, while appending a `fallback_reason` to the chunk's metadata.
