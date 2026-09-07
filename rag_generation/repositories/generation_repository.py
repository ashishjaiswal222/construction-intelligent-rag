import logging
from typing import Optional, List
from rag_generation.models.generation_log import GenerationLog

logger = logging.getLogger(__name__)

class GenerationRepository:

    def save_log(
        self,
        project_id: str,
        user_query: str,
        answer: str,
        confidence: float,
        answer_grounded: bool,
        needs_fallback: bool,
        chunks_used: int,
        chunk_ids_used: list[str],
        filter_used: dict,
        stages_completed: list[str],
        retrieval_ms: int,
        generation_ms: int,
        model_used: str,
        warning_message: str,
    ) -> Optional[GenerationLog]:
        """
        ORM create on GenerationLog.
        Returns the saved instance.
        NEVER raises — log failure must never break the response.
        Wraps in try/except; logs error and returns None on failure.
        """
        try:
            log = GenerationLog.objects.create(
                project_id=project_id,
                user_query=user_query,
                generated_answer=answer,
                confidence=confidence,
                answer_grounded=answer_grounded,
                needs_fallback=needs_fallback,
                chunks_used=chunks_used,
                chunk_ids_used=chunk_ids_used,
                filter_used=filter_used,
                stages_completed=stages_completed,
                retrieval_ms=retrieval_ms,
                generation_ms=generation_ms,
                model_used=model_used,
                warning_message=warning_message,
            )
            return log
        except Exception as e:
            logger.error(f"Failed to save GenerationLog: {str(e)}")
            return None

    def get_recent_logs(
        self,
        project_id: str,
        limit: int = 20,
    ) -> List[GenerationLog]:
        """
        ORM query on GenerationLog.
        Used by the audit API endpoint.
        Orders by created_at DESC.
        """
        try:
            return list(GenerationLog.objects.filter(project_id=project_id).order_by('-created_at')[:limit])
        except Exception as e:
            logger.error(f"Failed to get recent GenerationLogs for project {project_id}: {str(e)}")
            return []
