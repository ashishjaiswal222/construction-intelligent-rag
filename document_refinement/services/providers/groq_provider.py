from groq import Groq
import time
import logging

logger = logging.getLogger(__name__)

class GroqRepairProvider:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)

    def repair(self, prompt: str, retry_count: int = 0) -> str:
        """
        Calls Groq llama-3.1-8b-instant.
        Returns repaired text string.
        Raises exception on any failure.
        """
        # Sleep on initial attempt to prevent bulk bursting
        if retry_count == 0:
            time.sleep(2)
            
        response = self.client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=600,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
