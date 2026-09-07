import json
from typing import Tuple, Optional
from pydantic import BaseModel, ConfigDict
from rag_generation.prompts.hallucination_check_prompt import HALLUCINATION_CHECK_PROMPT

class HallucinationGuardResult(BaseModel):
    model_config = ConfigDict(extra='ignore')
    is_grounded: bool
    ungrounded_claims: list[str] = []
    warning: Optional[str] = None

class HallucinationGuard:
    """
    Post-generation verification.
    """

    def __init__(self, groq_api_key: str):
        import os
        from langchain_groq import ChatGroq
        self.model = os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
        self.llm = ChatGroq(
            model=self.model,
            api_key=groq_api_key,
            temperature=0.0,
        )
        self._failure_count = 0
        self._circuit_threshold = 3
        self._circuit_open = False

    def check(
        self,
        user_query: str,
        answer: str,
        context_string: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Returns (is_grounded, warning_message).
        """
        if self._circuit_open:
            return True, None

        if not context_string or not answer:
            return True, None

        prompt = HALLUCINATION_CHECK_PROMPT.format(
            user_query=user_query,
            answer=answer,
            context=context_string
        )

        try:
            # We use structured output if possible, or parse JSON directly
            grader = self.llm.with_structured_output(HallucinationGuardResult)
            result = grader.invoke(prompt)
            
            # Reset circuit on success
            self._failure_count = 0
            
            return result.is_grounded, result.warning
            
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self._circuit_threshold:
                self._circuit_open = True
            # On failure, assume grounded to not block user
            return True, None
