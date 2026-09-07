# Retrieval Strategies Deep Dive

The Construction Intelligence Platform employs several advanced RAG retrieval strategies to ensure high precision in highly technical construction terminology.

## 1. Reciprocal Rank Fusion (RRF)

**Why we use it:**
Construction documents often contain exact alphanumeric codes (e.g., `ASTM C39`, `Drawing A-104`). Vector search (Dense) is excellent at understanding concepts ("concrete strength"), but terrible at exact alphanumeric matching. BM25 (Sparse) is excellent at exact matching but terrible at concepts. 

RRF combines them mathematically:
```python
score = 1.0 / (k + rank_in_dense) + 1.0 / (k + rank_in_sparse)
```
*Where `k` is typically 60.*
Chunks that rank moderately high in *both* systems will outscore chunks that rank #1 in only one system.

## 2. Defaulting to `is_current=True`

**Why we use it:**
In construction, retrieving an old, superseded structural drawing or an old revision of a BOQ is a catastrophic error that could lead to physical rework. 

The `DenseSearchService` and `SparseSearchService` explicitly enforce `is_current=True` on *all* queries unless the user specifically uses terms like "superseded", "old", or "previous" in their natural language query (extracted via the `SelfQueryService`).

## 3. Parent-Child Chunk Expansion

**Why we use it:**
When chunking large contracts (Phase 4), a deeply nested clause (e.g., `1.4.2.a`) might just say: *"The Contractor shall bear these costs."* If retrieved in isolation, the LLM has no idea what "these costs" refers to.

Our `ExpansionService` inspects the retrieved chunks. If it identifies a `contract_clause` chunk type, it uses raw SQL to join the `document_chunking_documentchunk` table and retrieve `chunk_index - 1`. This safely pulls the parent clause into the context window without expanding the actual vector index size.

## 4. CRAG (Corrective Retrieval Augmented Generation)

**Why we use it:**
Vector similarity is not identical to logical relevance. Two sentences can share 95% of the same words but mean entirely different things, resulting in high Qdrant scores but useless context.

The `CRAGService` acts as a strict bouncer. It prompts an LLM (`llama-3.1`) to explicitly grade the chunk:
*"Does this extract directly answer or inform the query?"*
If the confidence is below 0.5, the chunk is silently dropped before Phase 8 ever sees it, drastically reducing hallucination rates and saving generation tokens.
