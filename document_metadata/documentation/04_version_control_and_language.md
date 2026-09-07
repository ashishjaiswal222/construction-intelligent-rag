# Phase 5: Version Control and Language

## 1. The Version Chain Manager

One of the most dangerous failure modes in Construction RAG is "version blindness"—when an LLM answers a question using an outdated, superseded drawing instead of the current one.

The `VersionChainManager` solves this.

**How it works:**
1. A new document finishes extraction. Groq identifies it as `Drawing S-023 Rev B`.
2. The `VersionChainManager` asks the database via `find_current_revision()`: "Do we have any document for this project with `drawing_number = S-023` and `is_current = True`?"
   - **CRITICAL**: This query *must* pass `exclude_document_id=document_id` (the ID of Rev B). Without this, if Celery retries the task, the document would query itself, mark itself as superseded, and silently delete itself from the vector search.
3. The database returns the UUID of `Rev A`.
4. The manager immediately updates `Rev A`, setting `is_current = False` and `superseded_by_id = [UUID of Rev B]`.
5. The new `Rev B` is saved with `is_current = True`.

This guarantees that at any given time, only one version of a specific drawing or specification is considered "current". When Phase 7 performs vector retrieval, it applies a hard database filter for `is_current=True`, eliminating outdated information entirely.

## 2. Chunk Backfilling

Metadata is stored at the Document level, but Vector search happens at the Chunk level (Phase 4).
Because of this, the `is_current` flag must exist on *every single chunk*.

Whenever the `VersionChainManager` updates a document's status, the Celery task triggers the `MetadataRepository.update_chunk_metadata()` method. This executes a raw SQL `UPDATE` against the Phase 4 `document_chunk` table, cascading the `is_current` boolean down to all 500+ chunks belonging to that document in milliseconds.

## 3. Language Detection

Construction in India frequently involves multilingual documents (e.g., English drawings with Hindi annotations).

The `LanguageDetector` service uses `langdetect` to sample the text.
- If it detects `hi`, `ur`, or `ar`, it flags the document as `hi`.
- If it detects `en` but finds more than 5 Unicode characters in the Hindi Unicode range (`0x0900 - 0x097F`), it flags the document as `mixed`.

This metadata allows the frontend UI to display translation warnings and helps Phase 7 know when to engage multilingual embedding models.
