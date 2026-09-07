from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Query metrics
QUERY_TOTAL = Counter('rag_queries_total', 'Total RAG queries', ['project_id', 'status'])
QUERY_LATENCY = Histogram('rag_query_latency_seconds', 'Query latency', ['stage'], buckets=[1,2,5,8,15,30])
RETRIEVAL_HITS = Counter('rag_retrieval_hits_total', 'Retrieval successes')
RETRIEVAL_MISS = Counter('rag_retrieval_misses_total', 'CRAG rejections')

# Token metrics
TOKENS_USED = Counter('llm_tokens_used_total', 'Total LLM tokens', ['model', 'type'])  # type: input/output
COST_USD = Counter('llm_cost_usd_total', 'Estimated LLM cost USD', ['model'])

# Document processing
DOCS_PROCESSED = Counter('docs_processed_total', 'Documents processed', ['doc_type', 'status'])
OCR_CONFIDENCE = Histogram('ocr_confidence', 'OCR confidence scores', buckets=[0.5,0.6,0.7,0.8,0.85,0.9,0.95,1.0])
QUEUE_DEPTH = Gauge('celery_queue_depth', 'Celery queue size', ['queue'])

def timed_query(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = fn(*args, **kwargs)
            project_id = kwargs.get('project_id', '')
            QUERY_TOTAL.labels(project_id=str(project_id), status='success').inc()
            QUERY_LATENCY.labels(stage='total').observe(time.time() - start)
            return result
        except Exception as e:
            project_id = kwargs.get('project_id', '')
            QUERY_TOTAL.labels(project_id=str(project_id), status='error').inc()
            raise e
    return wrapper
