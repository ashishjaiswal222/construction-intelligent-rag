import os
import logging
from document_retrieval.schemas.query_filters import QueryFilters
from document_retrieval.schemas.retrieval_result import RetrievedChunk

logger = logging.getLogger(__name__)

class DenseSearchService:
    def __init__(self, qdrant_path: str, embedding_api_key: str):
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        from langchain_community.embeddings import OllamaEmbeddings
        from shared.llms.custom_cohere_embeddings import CustomCohereEmbeddings as CohereEmbeddings
        from shared.services.qdrant_manager import QdrantManager
        
        self.client = QdrantManager.get_client(qdrant_path)
        
        cohere_key = os.environ.get('COHERE_API_KEY', '')
        gemini_key = os.environ.get('GEMINI_API_KEY', embedding_api_key)
        
        self.cohere_embeddings = CohereEmbeddings(
            api_key=cohere_key,
            model='embed-english-v3.0'
        ) if cohere_key else None
        
        self.gemini_embeddings = GoogleGenerativeAIEmbeddings(
            model='models/text-embedding-004',
            google_api_key=gemini_key,
        ) if gemini_key else None
        
        self.ollama_embeddings = OllamaEmbeddings(
            model='nomic-embed-text',
            base_url='http://127.0.0.1:11434'
        )

    def search(
        self,
        query: str,
        filters: QueryFilters,
        top_k: int = 15,
    ) -> list[RetrievedChunk]:
        """
        Embed query with all available models -> search all Qdrant collections -> combine chunks.
        """
        import concurrent.futures
        
        qdrant_filter = self._build_filter(filters)
        combined_results = []
        
        def _search_collection(model_impl, collection_name):
            try:
                if not model_impl:
                    return []
                vector = model_impl.embed_query(query)
                results = self.client.query_points(
                    collection_name=collection_name,
                    query=vector,
                    query_filter=qdrant_filter,
                    limit=top_k,
                    with_payload=True,
                ).points
                return [self._to_chunk(r) for r in results]
            except Exception as e:
                logger.error(f'Qdrant search failed on {collection_name}: {e}')
                return []

        # Run searches in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_cohere = executor.submit(_search_collection, self.cohere_embeddings, 'construction_cohere_1024')
            future_gemini = executor.submit(_search_collection, self.gemini_embeddings, 'construction_gemini_768')
            future_nomic = executor.submit(_search_collection, self.ollama_embeddings, 'construction_nomic_768')
            
            combined_results.extend(future_cohere.result())
            combined_results.extend(future_gemini.result())
            combined_results.extend(future_nomic.result())

        # Deduplicate
        seen = set()
        deduped = []
        for chunk in combined_results:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                deduped.append(chunk)
                
        # Sort by score descending
        deduped.sort(key=lambda x: x.score, reverse=True)
        return deduped[:top_k * 2] # Return slightly more for reranker

    def multi_query_search(
        self,
        queries: list[str],
        filters: QueryFilters,
        top_k_per_query: int = 15,
    ) -> list[RetrievedChunk]:
        """
        Run search for each query across all active collections.
        """
        if not queries:
            return []
            
        import concurrent.futures
        qdrant_filter = self._build_filter(filters)
        
        def _batch_search_collection(model_impl, collection_name):
            try:
                if not model_impl:
                    return []
                vectors = model_impl.embed_documents(queries)
                collection_chunks = []
                for vector in vectors:
                    results = self.client.query_points(
                        collection_name=collection_name,
                        query=vector,
                        query_filter=qdrant_filter,
                        limit=top_k_per_query,
                        with_payload=True,
                    ).points
                    collection_chunks.extend([self._to_chunk(r) for r in results])
                return collection_chunks
            except Exception as e:
                logger.error(f'Qdrant multi search failed on {collection_name}: {e}')
                return []

        combined = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            future_cohere = executor.submit(_batch_search_collection, self.cohere_embeddings, 'construction_cohere_1024')
            future_gemini = executor.submit(_batch_search_collection, self.gemini_embeddings, 'construction_gemini_768')
            future_nomic = executor.submit(_batch_search_collection, self.ollama_embeddings, 'construction_nomic_768')
            
            combined.extend(future_cohere.result())
            combined.extend(future_gemini.result())
            combined.extend(future_nomic.result())

        seen = set()
        deduped = []
        for chunk in combined:
            if chunk.chunk_id not in seen:
                seen.add(chunk.chunk_id)
                deduped.append(chunk)
                
        return deduped

    def _build_filter(self, filters: QueryFilters):
        from qdrant_client.http.models import (
            Filter, FieldCondition, MatchValue
        )
        conditions = []

        is_current = filters.is_current
        if is_current is None:
            is_current = True
        conditions.append(
            FieldCondition(
                key='metadata.is_current',
                match=MatchValue(value=is_current)
            )
        )

        if filters.project_id:
            conditions.append(FieldCondition(
                key='metadata.project_id',
                match=MatchValue(value=filters.project_id)
            ))
        if filters.doc_type:
            conditions.append(FieldCondition(
                key='metadata.doc_type',
                match=MatchValue(value=filters.doc_type)
            ))
        if filters.discipline:
            conditions.append(FieldCondition(
                key='metadata.discipline',
                match=MatchValue(value=filters.discipline)
            ))
        if filters.floor_level:
            conditions.append(FieldCondition(
                key='metadata.floor_level',
                match=MatchValue(value=filters.floor_level)
            ))
        if filters.drawing_number:
            conditions.append(FieldCondition(
                key='metadata.drawing_number',
                match=MatchValue(value=filters.drawing_number)
            ))

        return Filter(must=conditions) if conditions else None

    def _to_chunk(self, result) -> RetrievedChunk:
        # In internal API we changed payload schema: payload={'page_content': ..., 'metadata': {...}}
        p = result.payload or {}
        meta = p.get('metadata', p) # Fallback if old schema
        
        return RetrievedChunk(
            chunk_id=str(result.id),
            content=p.get('page_content', meta.get('content', '')),
            doc_type=meta.get('doc_type', ''),
            document_id=meta.get('document_id', ''),
            project_id=meta.get('project_id', ''),
            filename=meta.get('filename', ''),
            revision=meta.get('revision', ''),
            is_current=bool(meta.get('is_current', True)),
            drawing_number=meta.get('drawing_number'),
            clause_number=meta.get('clause_number'),
            page_number=meta.get('page_number'),
            chunk_type=meta.get('chunk_type', 'generic'),
            score=result.score or 0.0,
        )
