import os
from langchain_ollama import ChatOllama
from ..schemas.classification import DocumentClassification
from ..prompts.classification_prompt import CLASSIFICATION_PROMPT

class LLMClassifierService:
    def __init__(self):
        # Layer 2: Fast local LLM via Ollama
        self.fast_llm = ChatOllama(model='llama3.1', temperature=0.0)
        # We can keep a slightly more capable model for quality escalation if needed, or just use the same
        self.qual_llm = ChatOllama(model='llama3.1', temperature=0.0)

    def classify(self, filename: str, file_type: str, page_count: int, preview: str) -> DocumentClassification:
        prompt = CLASSIFICATION_PROMPT.format(
            filename=filename, 
            file_type=file_type, 
            page_count=page_count, 
            preview=preview[:2500]
        )
        
        try:
            # Layer 2: Fast LLM (Ollama)
            result = self.fast_llm.with_structured_output(DocumentClassification).invoke(prompt)
            
            # Layer 3: If uncertain, escalate (Currently still Ollama, but could be swapped)
            if result.confidence < 0.75:
                result = self.qual_llm.with_structured_output(DocumentClassification).invoke(prompt)
                
            return result
        except Exception as e:
            raise RuntimeError(f"LLM Classification failed: {e}")
