import os
import time
from typing import Any, Type, Dict, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, model_name: str = 'gemini-2.5-flash'):
        self.model_name = model_name
        self.client = ChatGoogleGenerativeAI(model=self.model_name, google_api_key=os.environ.get('GEMINI_API_KEY'))

    def analyze_structured(self, prompt: str, schema: Type) -> Tuple[Any, Dict[str, Any]]:
        start_time = time.time()
        
        llm_with_structured_output = self.client.with_structured_output(schema)
        result = llm_with_structured_output.invoke(prompt)
        
        end_time = time.time()
        latency = end_time - start_time
        
        # Approximate tokens
        tokens_in = len(prompt) // 4
        tokens_out = len(str(result.model_dump())) // 4 
        
        # Gemini Flash cost estimation
        cost = ((tokens_in + tokens_out) / 1000000) * 0.075
        
        usage = {
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'cost': cost,
            'model': self.model_name,
            'latency': latency
        }
        
        return result, usage
