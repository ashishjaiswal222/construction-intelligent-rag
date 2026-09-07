import cohere
from typing import List

class CustomCohereEmbeddings:
    """
    A lightweight wrapper around the official Cohere v7 client to provide
    a Langchain-compatible Embeddings interface.
    """
    def __init__(self, api_key: str, model: str = 'embed-english-v3.0'):
        self.client = cohere.Client(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embed(
            texts=texts,
            model=self.model,
            input_type="search_document"
        )
        return response.embeddings

    def embed_query(self, text: str) -> List[float]:
        response = self.client.embed(
            texts=[text],
            model=self.model,
            input_type="search_query"
        )
        return response.embeddings[0]
