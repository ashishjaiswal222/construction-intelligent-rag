from .base import BaseLLMProvider
from .groq_provider import GroqProvider
from .gemini_provider import GeminiProvider
from shared.reliability.circuit_breaker import RedisCircuitBreaker

class CircuitBreakerProviderProxy(BaseLLMProvider):
    def __init__(self, provider: BaseLLMProvider, provider_name: str):
        self._provider = provider
        # Create a circuit breaker with 3 failures max before opening
        self._breaker = RedisCircuitBreaker(name=provider_name, failure_threshold=3, reset_timeout=30)
        
    def generate(self, prompt: str, **kwargs) -> tuple[str, dict]:
        def call_provider():
            return self._provider.generate(prompt, **kwargs)
        return self._breaker.call(call_provider)
        
    def analyze_structured(self, prompt: str, pydantic_schema, **kwargs) -> tuple:
        def call_provider():
            return self._provider.analyze_structured(prompt, pydantic_schema, **kwargs)
        return self._breaker.call(call_provider)

class LLMFactory:
    @staticmethod
    def get_provider(provider_name: str, **kwargs) -> BaseLLMProvider:
        if provider_name.lower() == 'groq':
            provider = GroqProvider(**kwargs)
        elif provider_name.lower() == 'gemini':
            provider = GeminiProvider(**kwargs)
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")
            
        return CircuitBreakerProviderProxy(provider, provider_name.lower())
