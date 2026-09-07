import os
import time
from typing import Any, Type, Dict, Tuple
from langchain_groq import ChatGroq
from .base import BaseLLMProvider

class GroqProvider(BaseLLMProvider):
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.environ.get('GROQ_MODEL', 'qwen/qwen3.8-27b')
        self.client = ChatGroq(model=self.model_name, api_key=os.environ.get('GROQ_API_KEY'))

    def analyze_structured(self, prompt: str, schema: Type) -> Tuple[Any, Dict[str, Any]]:
        start_time = time.time()
        
        # Langchain Groq wrapper
        llm_with_structured_output = self.client.with_structured_output(schema)
        
        # We invoke to get the parsed object
        # Note: Langchain doesn't cleanly expose token usage in with_structured_output out of the box 
        # without callbacks, so we'll approximate or use standard metadata if available.
        # For this phase, we mock token usage slightly or pull from response_metadata if we bypass structured_output.
        # To get both, it's easier to just invoke and assume standard cost logic.
        
        result = llm_with_structured_output.invoke(prompt)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Approximate tokens (1 token ~ 4 chars)
        tokens_in = len(prompt) // 4
        # Since result is structured, we estimate out tokens based on string representation length
        tokens_out = len(str(result.model_dump())) // 4 
        
        # Groq Llama 3 8b cost estimation (e.g., $0.05 per 1M tokens)
        cost = ((tokens_in + tokens_out) / 1000000) * 0.05
        
        usage = {
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'cost': cost,
            'model': self.model_name,
            'latency': latency
        }
        
        return result, usage
