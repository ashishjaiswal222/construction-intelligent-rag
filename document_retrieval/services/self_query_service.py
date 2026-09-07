import logging
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.prompts.self_query_prompt import SELF_QUERY_PROMPT

logger = logging.getLogger(__name__)

class SelfQueryService:
    def __init__(self, groq_api_key: str):
        import os
        from langchain_groq import ChatGroq
        model = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
        self.llm = ChatGroq(
            model=model,
            api_key=groq_api_key,
            temperature=0.0,
        )

    def extract_filters(self, user_query: str) -> QueryFilters:
        """
        Reads natural language query.
        Extracts metadata filters AND generates 3 sub-queries.
        NEVER raises — returns minimal QueryFilters on any failure.
        """
        try:
            return self.llm.with_structured_output(
                QueryFilters
            ).invoke(
                SELF_QUERY_PROMPT.format(query=user_query)
            )
        except Exception as e:
            logger.warning(
                f'Self-query extraction failed: {e}. '
                f'Using raw query as semantic_query.'
            )
            return QueryFilters(
                semantic_query=user_query,
                sub_queries=[user_query, user_query, user_query],
            )
