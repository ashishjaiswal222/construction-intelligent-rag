# Phase 8: Pipeline Flow & Data Lifecycle

The Generation Pipeline is triggered via a synchronous API call to `POST /api/generate/`.

## The 4-Step Lifecycle

### Step 1: Retrieval Handoff (Phase 7 → Phase 8)
- The user query hits the API.
- The view immediately calls `_retrieval_pipeline.retrieve(query)`.
- Phase 7 runs its 6-stage semantic search (Self-Query, Dense, Sparse, Fusion, Expansion, CRAG Grading).
- It returns a `RetrievalResult` schema containing a list of `RetrievedChunk` objects.
- This result is passed into the `GenerationPipeline`.

### Step 2: Context Building
- `ContextBuilder` takes the chunks and formats them.
- It truncates the context precisely at 6000 characters to prevent the LLM from losing "needle-in-a-haystack" focus.
- It generates an ordered array of `Citation` models matching the `[SOURCE n]` labels embedded in the context string.

### Step 3: LLM Generation
- The `GeneratorService` injects the 6000-char context and the user query into the `GENERATION_PROMPT`.
- The prompt explicitly forces the LLM to output numeric citation markers `[1]`, `[2]` corresponding to its factual claims.
- The LLM returns a raw markdown string.

### Step 4: Verification & Logging
- The `HallucinationGuard` takes the generated answer and the 6000-char context string.
- It runs a parallel LLM process evaluating if the answer invented any claims.
- The pipeline calculates a mathematical `confidence` score (0.0 to 1.0) based on how many chunks were used vs provided, scaled by their initial dense/sparse retrieval scores.
- The pipeline saves a `GenerationLog` to PostgreSQL.
- Finally, it returns a `GenerationResponse` payload to the frontend.

## Fallback Mechanism
If Phase 7 returns `needs_fallback=True` (meaning it failed to find a precise match and had to loosen its metadata filters to find "related" documents):
1. The `confidence` score is hard-capped at a maximum of `0.6`.
2. The `GeneratorService` swaps to the `FALLBACK_GENERATION_PROMPT`.
3. The LLM is forced to begin its response with a disclaimer stating it is answering based on the closest available, but non-exact, information.
