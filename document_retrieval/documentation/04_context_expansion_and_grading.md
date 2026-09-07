# Document Retrieval: 04 Context Expansion & Grading

This document explains the final, highly advanced stages of the pipeline designed to completely eliminate AI hallucination before it occurs.

## 1. Parent-Child Expansion (`expansion_service.py`)

A major flaw in naive RAG systems is the "Loss of Context" during chunking. 
If a 100-page FIDIC contract is chopped into 500-word chunks, the dependencies break. 

**Example:**
*Chunk 44 (Parent):* "In the event of a Category 3 weather delay..."
*Chunk 45 (Child):* "...the Contractor shall be granted a 5-day extension without financial compensation."

If a user asks *"Do I get paid for a weather delay?"*, Vector search will retrieve Chunk 45. But the AI won't know that it only applies to Category 3 delays!

### The SQL Solution
Instead of importing the massive `document_chunking` Django models, we execute a lightning-fast raw SQL query inside `retrieval_repository.py`.

If `expansion_service` sees a retrieved chunk with `chunk_type == 'contract_clause'`, it asks the database for `chunk_index - 1` belonging to the same `document_id`. 
It safely appends the Parent chunk to the retrieval list, giving the final AI the entire legal context it needs to answer safely.

## 2. Corrective Retrieval Augmented Generation (CRAG)

Retrieval systems are inherently flawed: they will *always* return the "most similar" text they can find, even if that text has absolutely nothing to do with the question.

### The Grader (`crag_service.py`)
To fix this, we implement CRAG. We take the top 8 reranked chunks and feed them individually to Groq (`llama-3.1-8b-instant`) with a strict prompt:
> *"Grade strictly. A chunk is relevant ONLY if it contains information that directly helps answer the query. Tangentially related content is NOT relevant."*

The LLM outputs a `RelevanceGrade` schema:
```json
{
  "is_relevant": false,
  "confidence": 0.95,
  "reason": "The chunk discusses concrete curing times, not compressive strength requirements."
}
```
If `is_relevant` is false, the chunk is instantly purged from the pipeline.

### The Fallback Mechanism
If the user asks a very specific question (e.g., *"Show me the door schedules for Level 2"*), but they accidentally applied a filter (e.g., they selected `doc_type: "contract"` in the UI), the database will find 0 relevant chunks.

When the CRAG grader deletes all 8 chunks, it returns `needs_fallback = True`. 
The orchestrator (`retrieval_pipeline.py`) catches this flag. It realizes the filters were too strict. It deletes the `doc_type`, `discipline`, and `floor_level` filters, and runs a secondary "loose" vector search, attempting to gracefully recover the answer before telling the user "I don't know."
