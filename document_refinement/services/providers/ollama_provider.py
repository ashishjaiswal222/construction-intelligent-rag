class OllamaRepairProvider:
    def __init__(self, base_url: str = 'http://localhost:11434'):
        self.base_url = base_url
        self.model = 'llama3.1'

    def is_available(self) -> bool:
        """Check if Ollama server is running."""
        try:
            import httpx
            r = httpx.get(f'{self.base_url}/api/tags', timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def repair(self, prompt: str) -> str:
        """
        Calls local Ollama llama3.2 model.
        Returns repaired text string.
        Raises exception on any failure.
        Uses httpx, not ollama Python SDK, for fewer deps.
        """
        import httpx
        response = httpx.post(
            f'{self.base_url}/api/generate',
            json={
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0.1, 'num_predict': 600},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()['response'].strip()
