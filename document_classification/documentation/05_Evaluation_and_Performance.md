# Evaluation, Metrics, & Performance Tuning

To ensure the classifier remains highly accurate and cost-effective as new documents are added, the pipeline includes a fully automated evaluation suite (`test_comprehensive_eval.py`).

## Automated Evaluation Suite

The script is a standalone Python client that simulates frontend user behavior but hooks directly into the Django environment to pull deep analytics.

### How It Works
1.  **Database Reset**: `clear_database()` runs first, dropping all previous `Document`, `Fingerprint`, and `LLMUsageLog` records from PostgreSQL to ensure a clean slate.
2.  **Ingestion**: It iterates through `sample_documents_classification/`, maps each file to its true ground truth label (`GROUND_TRUTH_SAMPLE`), and uploads them via the POST `/api/documents/upload/` endpoint.
3.  **Polling**: It pings the `/status/` endpoint waiting for the asynchronous Celery workers to finish.
4.  **Metric Calculation**: Once all files are processed, it calculates standard ML metrics (Precision, Recall, F1) across the confusion matrix.

### The Production Gates
To pass the evaluation, the system must hit the following strict gates:
*   Overall Accuracy: `> 90%`
*   Drawing Precision: `> 95%` (Because drawings require an entirely different OCR pipeline)
*   Contract Precision: `> 98%` (Because legal documents are high-liability)
*   Per-Class Precision/Recall: `> 85%`

---

## Bottleneck Analysis & Speed Improvements

During initial testing, the evaluation script took over **300 seconds** to process 12 files. Analysis revealed that the fundamental bottleneck was **not** the LLM. 

### Why It Was Slow
1.  **Synchronous Polling**: The test script uploads one file, waits for it to finish, and *then* uploads the next.
2.  **Exponential Backoff Stalls**: When the Groq LLM hallucinated parsing keys on an `RFP` document, it triggered the fallback Gemini LLM. Because Gemini hit a `429 Quota Exceeded` rate limit on the free tier, Celery caught the error and triggered a 60-second backoff delay. The synchronous test script sat and waited for 60 seconds just for that one document.

### Speed Improvements Implemented
To process documents at massive scale, the platform utilizes:

1.  **Parallel Batch Ingestion (Implemented)**: The test script now uses Python's `concurrent.futures.ThreadPoolExecutor(max_workers=12)`. Instead of waiting for a file to process, it uploads all 12 files concurrently. Celery's `concurrency=12` setting allows it to classify all 12 files simultaneously. This drops processing time from 300+ seconds down to ~4-5 seconds.
2.  **Heuristics First (Implemented)**: By adding `RFP`, `RFI`, and `Spreadsheet` filters to the `HeuristicClassifierService`, we completely bypass the LLM. Heuristics take `0.005 seconds` to run versus the LLM's `0.78 seconds`, eliminating rate limits and token costs for standard files.

## Future Enhancements: Why We Skipped WebSockets (For Now)
During architectural planning, we considered replacing the HTTP polling system (`time.sleep(1)`) with **Django Channels (WebSockets)** to push the `classification_completed` signal instantly to the UI.

**Decision: Deferred to Phase 2**
We have explicitly chosen *not* to implement WebSockets in the current architecture. 
* **The Problem is Solved**: By implementing Asynchronous Batch Ingestion, a massive batch of documents now processes in ~4 seconds. The 1-second overhead of HTTP polling is no longer a critical bottleneck.
* **Architectural Complexity**: WebSockets require replacing the stable WSGI server with an ASGI server (Daphne), managing long-lived connections, and handling complex load balancer configurations during cloud deployment.
* **Next Steps**: WebSockets will remain a "Future Enhancement" reserved for when we build a highly interactive, real-time React frontend that specifically demands a "Wow Factor" for live document updates. Until then, the current architecture is highly stable and blazing fast.

## Analyzing PostgreSQL Metrics
After running the evaluation script, you can query the exact cost and token usage of your pipeline:

```python
# Fetches the total amount of money spent classifying this batch of documents
from document_classification.models.audit import LLMUsageLog
from django.db.models import Sum

total_cost = LLMUsageLog.objects.aggregate(Sum('cost'))['cost__sum']
print(f"Cost: ${total_cost}")
```
For a 12-document batch using Groq's LLaMA-3.1-8b, the average pipeline cost is roughly **$0.00044**, demonstrating massive scalability.
