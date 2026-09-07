# Document Retrieval: 01 Architecture Overview

The `document_retrieval` application (Phase 7) serves as the **Synchronous, Query-Time Engine** of the Construction Intelligence Platform. Unlike Phases 1-6, which are asynchronous and handled by Celery workers, Phase 7 executes in real-time when a user submits a query.

Its singular goal is to extract the absolute best, most factually correct chunks from the database and feed them to the RAG Generator (Phase 8), eliminating hallucination at the source.

---

## 1. Core Architectural Constraints

Phase 7 was built under extreme architectural constraints to guarantee safety, modularity, and high performance:

### ❌ What is FORBIDDEN in this phase:
- **No Celery Tasks**: Retrieval must be instantaneous and synchronous.
- **No ORM Imports from other apps**: Retrieving chunk data relies entirely on isolated raw SQL queries. We do not import `DocumentChunk` from `document_chunking`.
- **No Direct Business Logic in Views**: API views only serialize requests and pass them to the pipeline orchestrator.
- **No Loose Dictionaries**: All data traversing the pipeline is strictly bound to Pydantic v2 schemas (`ConfigDict(extra='forbid')`).

### ✅ What is ENFORCED in this phase:
- **Dependency Injection**: The `RetrievalPipeline` accepts 6 isolated services in its constructor. This makes testing 100% mocked and reliable.
- **Module-Level Initialization**: The `RetrievalPipeline` (and the massive BM25 index it relies on) is initialized *once* at the module level in `api/views.py`. This prevents Python from reloading a gigabyte-sized BM25 file on every HTTP request.
- **Graceful Degradation**: Every single service has `try/except` blocks. If an API (like Cohere or Groq) goes down or rate-limits, the pipeline falls back to less advanced but still functional retrieval methods without throwing a 500 server error.

---

## 2. Directory Structure

```text
document_retrieval/
├── api/
│   ├── serializers.py      # Validates incoming queries
│   ├── views.py            # DRF endpoints & Pipeline Singleton
│   └── urls.py
├── schemas/
│   ├── query_filters.py    # Structured output from Self-Query
│   ├── relevance_grade.py  # Structured output from CRAG Grader
│   └── retrieval_result.py # Final payload sent to Phase 8
├── services/
│   ├── retrieval_pipeline.py    # The 6-stage Orchestrator
│   ├── self_query_service.py    # Stage 1: Groq Filter Extraction
│   ├── dense_search_service.py  # Stage 2A: Qdrant Vector Search
│   ├── sparse_search_service.py # Stage 2B: BM25 Keyword Search
│   ├── fusion_service.py        # Stage 3: RRF Blending
│   ├── expansion_service.py     # Stage 4: Parent-Child Context
│   ├── reranking_service.py     # Stage 5: Cohere Cross-Encoder
│   └── crag_service.py          # Stage 6: Groq Relevance Check
├── repositories/
│   └── retrieval_repository.py  # Raw SQL to fetch parent chunks
├── prompts/
│   ├── self_query_prompt.py     # Instructions for Stage 1
│   └── crag_grading_prompt.py   # Instructions for Stage 6
└── tests/                       # 100% coverage via pytest
```

---

## 3. High-Level Data Flow

1. **User Input**: The user sends a natural language question (e.g., *"What is the rebar sizing for the grade beams?"*).
2. **Translation**: The AI translates this into a machine-readable query with filters.
3. **Retrieval**: The system queries the Vector DB and Keyword DB.
4. **Scoring & Fusion**: The results are combined and scored mathematically.
5. **Context Expansion**: Missing context (like parent clauses) is fetched via SQL.
6. **Reranking**: A specialized model re-evaluates the chunks against the user's question.
7. **Verification**: A final AI reads the chunks and deletes any that don't actually answer the question.
8. **Output**: The surviving chunks are returned to the frontend or sent to the Phase 8 Generator.
