# API Endpoints: Document Retrieval

The retrieval pipeline is exposed via a standard Django DRF API interface. It is instantiated globally at the module level to ensure the massive `rank_bm25` index remains loaded in RAM across requests.

## 1. Standard Query Endpoint

**`POST /api/retrieval/query/`**

This is the primary endpoint to be consumed by the Phase 8 Generation engine.

**Request Body:**
```json
{
  "query": "What is the compressive strength requirement for foundation concrete?",
  "project_id": "PROJ-774A" // Optional
}
```

**Response (200 OK):**
Returns only the essential chunk data needed for generation.
```json
{
  "chunks": [
    {
      "chunk_id": "uuid-...",
      "content": "Concrete for foundations shall possess a minimum compressive strength of 35 MPa...",
      "doc_type": "specification",
      "document_id": "uuid-...",
      "project_id": "PROJ-774A",
      "filename": "Structural_Specs_Rev2.pdf",
      "revision": "2",
      "is_current": true,
      "page_number": 42,
      "chunk_type": "text",
      "score": 0.0321
    }
  ],
  "needs_fallback": false
}
```

## 2. Debug Query Endpoint

**`POST /api/retrieval/query/debug/`**

Exposes the internal mechanics of the pipeline. Excellent for testing if self-query extraction or CRAG grading is working as intended.

**Request Body:**
```json
{
  "query": "What is the compressive strength requirement for foundation concrete?"
}
```

**Response (200 OK):**
```json
{
  "chunks": [...],
  "needs_fallback": false,
  "filter_used": {
    "project_id": null,
    "doc_type": null,
    "is_current": true,
    "semantic_query": "compressive strength requirement for foundation concrete",
    "sub_queries": [
      "foundation concrete strength",
      "concrete MPa requirement",
      "structural concrete specifications"
    ]
  },
  "candidates_found": 34,
  "final_count": 5,
  "stages_completed": [
    "self_query",
    "hybrid_retrieval",
    "rrf_fusion",
    "parent_child_expansion",
    "cohere_reranking",
    "crag_grading"
  ],
  "processing_ms": 2450
}
```

## 3. Health Check

**`GET /api/retrieval/health/`**

Validates connection to Qdrant and ensures the BM25 singleton has been successfully loaded into memory from disk.

**Response (200 OK):**
```json
{
  "status": "ok",
  "qdrant": true,
  "bm25_loaded": true,
  "bm25_chunk_count": 14205
}
```
