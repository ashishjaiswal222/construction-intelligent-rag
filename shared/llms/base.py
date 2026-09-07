from abc import ABC, abstractmethod
from typing import Any, Type, Dict, Tuple

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def analyze_structured(self, prompt: str, schema: Type) -> Tuple[Any, Dict[str, Any]]:
        """
        Analyze prompt and return structured output according to Pydantic schema,
        along with usage statistics (tokens, cost).
        
        Returns:
            Tuple[schema_instance, usage_dict]
        """
        pass
