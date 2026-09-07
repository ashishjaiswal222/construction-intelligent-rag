import os
import time
import logging
from typing import List, Tuple
from django.core.cache import cache
from document_indexing.schemas.chunk_payload import ChunkPayload

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, api_key: str):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_community.embeddings import OllamaEmbeddings
        from shared.llms.custom_cohere_embeddings import CustomCohereEmbeddings as CohereEmbeddings
        
        # Load API keys
        cohere_key = os.environ.get('COHERE_API_KEY', '')
        gemini_key = os.environ.get('GEMINI_API_KEY', api_key)
        
        self.cohere_embeddings = None # Disabled to enforce Gemini/Nomic usage
        
        self.gemini_embeddings = GoogleGenerativeAIEmbeddings(
            model='models/text-embedding-004',
            google_api_key=gemini_key,
        ) if gemini_key else None
        
        self.ollama_embeddings = OllamaEmbeddings(
            model='nomic-embed-text',
            base_url='http://127.0.0.1:11434'
        )

    def embed_batch(self, texts: List[str], document_id: str) -> Tuple[List[List[float]], int, str]:
        """
        Embeds a batch of texts using three-tier fallback.
        Returns: (vectors, rate_limit_waits, model_used)
        """
        waits = 0
        
        # 1. Try Cohere
        if self.cohere_embeddings:
            try:
                vectors = self.cohere_embeddings.embed_documents(texts)
                return vectors, waits, "cohere"
            except Exception as e:
                logger.warning(f"Cohere failed for document {document_id}: {e}. Falling back to Gemini.")

        # 2. Try Gemini
        if self.gemini_embeddings:
            try:
                vectors = self.gemini_embeddings.embed_documents(texts)
                return vectors, waits, "gemini"
            except Exception as e:
                logger.warning(f"Gemini failed for document {document_id}: {e}. Falling back to Ollama.")
                
        # 3. Try Ollama (Offline)
        try:
            vectors = self.ollama_embeddings.embed_documents(texts)
            return vectors, waits, "nomic"
        except Exception as e:
            logger.error(f"All embedding providers failed for document {document_id}. Last error: {e}")
            raise Exception(f"Failed to embed batch: {e}")

    def embed_chunks_batched(self, payloads: List[ChunkPayload], document_id: str, batch_size: int = 100) -> Tuple[List[List[float]], int, str]:
        if not payloads:
            return [], 0, "cohere"
            
        all_embeddings = []
        total_waits = 0
        first_model = None

        for i in range(0, len(payloads), batch_size):
            batch = payloads[i:i+batch_size]
            texts = [p.preprocessed_text for p in batch]
            
            # Stick to the same model if we already fell back
            if first_model == "nomic":
                vectors = self.ollama_embeddings.embed_documents(texts)
                all_embeddings.extend(vectors)
                continue
            elif first_model == "gemini":
                # We skip Cohere this time but still try Gemini then Ollama
                try:
                    vectors = self.gemini_embeddings.embed_documents(texts)
                    all_embeddings.extend(vectors)
                    continue
                except:
                    first_model = "nomic"
                    vectors = self.ollama_embeddings.embed_documents(texts)
                    all_embeddings.extend(vectors)
                    continue

            vectors, waits, model_used = self.embed_batch(texts, document_id)
            all_embeddings.extend(vectors)
            total_waits += waits
            
            if not first_model:
                first_model = model_used
                
        return all_embeddings, total_waits, first_model
