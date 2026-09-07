# Phase 8: RAG Generation Architecture

The `rag_generation` application is the final component of the Construction Intelligence Platform. It sits cleanly on top of the Phase 7 Retrieval pipeline, taking the user's natural language query and the retrieved semantic chunks, and synthesizing them into a grounded, hallucination-free answer.

## Core Design Principles
1. **Zero Hallucination Tolerance**: Construction data is high-liability. The pipeline is designed to "warn, but not block" if it suspects the LLM has invented a claim.
2. **Synchronous Execution**: Unlike indexing phases, Generation happens at query-time while the user waits. Execution must be highly concurrent, latency-optimized, and free of Celery background jobs.
3. **Clean Architecture**: `views.py` (API Layer) → `services/` (Business Logic Layer) → `repositories/` (Data Access Layer). 
4. **Pydantic Validation**: Strict schemas (`ConfigDict(extra='forbid')`) govern the handoff between Retrieval and Generation.

## Component Overview

### `ContextBuilder`
Takes the `RetrievedChunk` objects from Phase 7, sorts them by score, and formats them into a bounded 6000-character context string. It ensures every chunk is explicitly labeled with its `[SOURCE n]`, `filename`, `revision`, and `drawing/clause number`.

### `GeneratorService`
Wraps Langchain and Groq (`llama-3.1-8b-instant`). It operates using two strict prompt templates:
- `GENERATION_PROMPT`: Demands inline citations (e.g. `[1]`) matching the source labels.
- `FALLBACK_GENERATION_PROMPT`: Triggers if Phase 7 set `needs_fallback=True`. It forces the LLM to begin its answer by explicitly stating that an exact match was not found.

### `HallucinationGuard`
A secondary, parallel LLM call that verifies the generated answer against the source context. It enforces structural grounding. If the LLM invents a strength grade or misattributes a dimension, the Guard detects it, sets `answer_grounded=False`, and attaches a warning message. 

### `GenerationRepository` & `GenerationLog`
A comprehensive PostgreSQL audit trail. Every query, generated answer, confidence score, and processing millisecond is logged for future quality-assurance review and potential model fine-tuning.
