import argparse
import json

def total_cost_model(
    daily_active_users: int,
    queries_per_user: float = 5.0,
    docs_to_process: int = 5000,
    pages_per_doc: float = 80.0,
    include_ocr: bool = True,
    llm_tier: str = 'free',  # 'free', 'mixed', 'paid'
) -> dict:
    queries_per_day = daily_active_users * queries_per_user
    queries_per_month = queries_per_day * 30
    total_pages = docs_to_process * pages_per_doc

    # Cost Assumptions
    ocr_cost_per_page = 0.0015 if include_ocr else 0.0
    embedding_cost_per_1m_tokens = 0.02
    llm_cost_per_1m_tokens = 0.50 if llm_tier == 'paid' else (0.10 if llm_tier == 'mixed' else 0.0)

    # Calculation
    # Assume 500 tokens per page
    total_tokens_processed = total_pages * 500
    
    ocr_total = total_pages * ocr_cost_per_page
    embedding_total = (total_tokens_processed / 1_000_000) * embedding_cost_per_1m_tokens
    
    # Assume 1000 tokens per query (prompt + response)
    query_tokens_per_month = queries_per_month * 1000
    llm_total = (query_tokens_per_month / 1_000_000) * llm_cost_per_1m_tokens

    monthly_infrastructure = 50.0  # Server, Redis, DB

    total_monthly_cost = ocr_total + embedding_total + llm_total + monthly_infrastructure

    return {
        "monthly_queries": int(queries_per_month),
        "total_pages_processed": int(total_pages),
        "costs_usd": {
            "ocr_processing": round(ocr_total, 2),
            "embeddings": round(embedding_total, 2),
            "llm_generation": round(llm_total, 2),
            "infrastructure": round(monthly_infrastructure, 2),
            "TOTAL_MONTHLY": round(total_monthly_cost, 2)
        }
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construction RAG Cost Estimator")
    parser.add_argument("--users", type=int, default=100, help="Daily active users")
    parser.add_argument("--docs", type=int, default=5000, help="Number of documents to process")
    parser.add_argument("--tier", type=str, choices=['free', 'mixed', 'paid'], default='paid', help="LLM usage tier")
    
    args = parser.parse_args()
    
    cost_breakdown = total_cost_model(
        daily_active_users=args.users,
        docs_to_process=args.docs,
        llm_tier=args.tier
    )
    
    print(json.dumps(cost_breakdown, indent=2))
