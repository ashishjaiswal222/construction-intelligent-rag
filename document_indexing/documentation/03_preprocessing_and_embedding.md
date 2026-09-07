# Preprocessing and Embeddings

## 1. Domain-Specific Preprocessing
Construction documents are laden with abbreviations (RFI, ITP, BOQ). If these are not normalized, an embedding model will struggle to map them correctly.
`TextPreprocessor` handles:
- **Abbreviations**: Expands terms like `RFI` to `Request for Information RFI`.
- **Units**: Normalizes `m3`, `CBM` to `cubic metres m3`.
- **Context Injection**: Prepends `"Construction {doc_type}: "` to all chunks. This grounds the LLM contextually, ensuring it views the chunk in the correct frame of reference.

## 2. Gemini `text-embedding-004`
We use Google Gemini's `text-embedding-004` model.
### Why Gemini?
- Dimensions: 768.
- Cost: Free up to 1500 RPM.
- Multilingual and capable of handling complex domain jargon.
- Storage: 768 dimensions uses significantly less memory (approx. 3.1 GB per 1M chunks) compared to OpenAI's 3072 dimension vectors (12.3 GB per 1M chunks). This is critical for scaling a local or cloud-based Vector DB cost-effectively.

### Batching and Resilience
The API can easily hit rate limits (429 Too Many Requests). The `EmbeddingService` implements:
- **Batched Requests**: 100 chunks at a time.
- **Exponential Backoff**: If a 429 is received, it waits 60s, then 120s, then 240s before failing.
- **Rate Limit Tracking**: Records exactly how many times it was paused to measure latency accurately.
