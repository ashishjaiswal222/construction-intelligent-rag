# Document Retrieval: 02 Pipeline Flow & Orchestration

This document walks through the exact lifecycle of a user query as it is processed by the `RetrievalPipeline` orchestrator.

## The Scenario

**User Query**: *"What is the compressive strength requirement for the foundation concrete on the Riverside project? Also show me the latest approved drawings."*

---

## Stage 1: Self-Query Extraction (`self_query_service.py`)

**What it does:** Uses `llama-3.1-8b` to parse the messy human query into hard data and focused sub-queries.

**Internal Flow:**
1. The user's query is injected into the `SELF_QUERY_PROMPT`.
2. Groq returns a structured `QueryFilters` object.
3. The Pipeline automatically enforces `is_current = True` to prevent retrieving superseded construction data.

**Example Output:**
```python
QueryFilters(
    project_id="Riverside",
    is_current=True,
    doc_type="drawing",
    semantic_query="compressive strength requirement foundation concrete",
    sub_queries=[
        "foundation concrete MPa",
        "structural concrete specifications",
        "foundation load bearing strength"
    ]
)
```

---

## Stage 2: Hybrid Search (Dense + Sparse)

**What it does:** Launches two concurrent searches against our vector databases and keyword indices.

### 2A. Dense Search (`dense_search_service.py`)
1. Generates a 768-dimensional vector using Gemini (`text-embedding-004`) for the `semantic_query` AND all 3 `sub_queries`.
2. Queries the `construction_docs` Qdrant collection.
3. **Payload Filter Applied:** `Must(project_id="Riverside", is_current=True, doc_type="drawing")`.
4. Returns the top 15 chunks per query.

### 2B. Sparse Search (`sparse_search_service.py`)
1. Tokenizes the user's raw query and compares it against the RAM-loaded `rank_bm25` index.
2. Identifies exact keyword hits (e.g., matching the exact word "Riverside" or "foundation").
3. Applies the metadata filters *in-memory* (post-search) to discard older revisions.
4. Returns the top 30 chunks.

---

## Stage 3: Fusion (`fusion_service.py`)

**What it does:** We now have two separate lists of chunks. Fusion blends them using Reciprocal Rank Fusion (RRF).

**Example:**
- Chunk A (A vector hit for "compressive strength") is #1 in Dense, #50 in Sparse.
- Chunk B (An exact text hit for "foundation concrete") is #5 in Dense, #2 in Sparse.
- **Result**: Chunk B gets the highest overall score because it successfully bridged the gap between semantic meaning and exact wording. 

The pipeline truncates the fused list down to the top 40 chunks.

---

## Stage 4: Parent-Child Expansion (`expansion_service.py`)

**What it does:** Prevents context loss in heavily nested legal or specification documents.

**Example:**
- The fusion list contains a chunk: `Chunk ID 99: "The Contractor shall bear these costs."` (Type: `contract_clause`)
- The pipeline realizes this is a useless chunk on its own.
- It executes raw SQL: `SELECT * FROM document_chunking_documentchunk WHERE chunk_index = 98 AND document_id = [Doc_ID]`
- It fetches the parent chunk (`Chunk ID 98: "If the foundation concrete fails the MPa test due to improper curing..."`) and quietly adds it to the list.

---

## Stage 5: Cohere Reranking (`reranking_service.py`)

**What it does:** Vector search is cheap but dumb. Cross-encoding is expensive but brilliant.

1. The pipeline sends the User's Query and all 40 expanded chunks to Cohere's `rerank-english-v3.0` API.
2. Cohere reads every word deeply and re-scores them.
3. It returns the definitive **Top 8 Chunks**.

*(Safety Feature: If Cohere fails 3 times in a row due to rate limits, a circuit breaker trips, and the pipeline gracefully skips this step, relying purely on the Stage 3 RRF scores).*

---

## Stage 6: CRAG Grading & Fallback (`crag_service.py`)

**What it does:** The final bouncer. It ensures no hallucinated context reaches the RAG generator.

1. The top 8 chunks are sent individually to `llama-3.1`.
2. The AI grades them: *"Does this chunk actually answer the user's query?"*
3. If 5 chunks are relevant, they proceed. The other 3 are deleted.

**The Fallback Safety Net:**
If the AI grades *all 8 chunks* as irrelevant (meaning our strict `project_id="Riverside", doc_type="drawing"` filters were too harsh), the pipeline sets `needs_fallback = True`. 
It loops back to Stage 2, deletes the `doc_type` filter, and searches again. It might find the answer in a "specification" document instead of a "drawing"!
