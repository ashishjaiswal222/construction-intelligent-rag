# Infrastructure: Redis & Celery Workers

Because processing PDFs and waiting for LLM API responses can take several seconds, the system offloads all work from the synchronous Django request/response cycle to asynchronous background workers.

## Message Broker: Redis
*   **Role**: Redis acts as both the message broker (passing task IDs from Django to Celery) and the result backend (storing task states).
*   **Networking Configuration**: During development on Windows, Redis binding to `localhost` occasionally caused DNS resolution timeouts in Python (`socket.gaierror`). To fix this, `core/settings.py` explicitly forces the IPv4 loopback address:
    ```python
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
    ```

## Task Execution: Celery Queue Routing
To prevent "Thundering Herd" issues where lightweight DB tasks get blocked behind heavy LLM tasks, the platform uses three distinct queues defined in `CELERY_TASK_ROUTES`:
1.  **`celery`**: The default queue for CPU/DB tasks (e.g., chunking, reconciliation).
2.  **`llm_gemini_queue`**: For tasks hitting the Google Gemini API (e.g., `process_page`, `extract_metadata_task`).
3.  **`llm_ollama_queue`**: For tasks hitting the local Ollama LLM (e.g., `classify_document_task`, `refine_page`).

### Windows Concurrency (Eventlet)
The pipeline uses **Eventlet** for async I/O.
*   **Execution Command**: `uv run celery -A core worker -l info -P eventlet -Q celery,llm_gemini_queue,llm_ollama_queue`
*   **Concurrency**: Workers use `concurrency=12` to handle multiple APIs without blocking.

### Resilience & Rate Limiting
To survive strict Free Tier limits (e.g., Gemini 15 RPM), the platform implements a dual-defense mechanism:

1.  **Native Celery Rate Limiting**: Tasks hitting Gemini (`process_page_task`, `extract_metadata_task`) are decorated with `rate_limit='15/m'`. Celery natively enforces this Token Bucket algorithm to prevent `429 Too Many Requests`.
2.  **Jittered Exponential Backoff**: If an API goes down, tasks trigger `raise self.retry` using a jittered backoff formula: `countdown = 60 * (2 ** retries) + random.uniform(0, 15)`. The random jitter ensures that sleeping tasks don't all wake up simultaneously to DDoS the API again.
