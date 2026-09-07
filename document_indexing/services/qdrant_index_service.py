import os
import logging
import requests
from typing import List, Dict, Any
from document_indexing.schemas.chunk_payload import ChunkPayload

logger = logging.getLogger(__name__)

COLLECTION_GEMINI = 'construction_gemini_768'
COLLECTION_NOMIC = 'construction_nomic_768'

# Use the internal Django URL so Celery can proxy Qdrant commands
INTERNAL_API_BASE = 'http://127.0.0.1:8000/api/indexing/internal/qdrant/'

class QdrantIndexService:
    def __init__(self, persist_directory: str, api_key: str):
        # We no longer instantiate QdrantClient here to avoid RocksDB locks in Celery!
        self.persist_directory = persist_directory

    def upsert_chunks(
        self,
        payloads: List[ChunkPayload],
        embeddings: List[List[float]],
        model_used: str = "gemini"
    ) -> int:
        if not payloads or not embeddings:
            return 0
            
        data = {
            "model_used": model_used,
            "payloads": [
                {
                    'document_id': str(p.document_id),
                    'chunk_id': p.chunk_id,
                    'doc_type': p.doc_type or '',
                    'doc_number': p.doc_number or '',
                    'title': p.title or '',
                    'revision': p.revision or '',
                    'is_current': p.is_current,
                    'approval_status': p.approval_status or '',
                    'project_id': p.project_id or '',
                    'project_name': p.project_name or '',
                    'project_phase': p.project_phase or '',
                    'building': p.building or '',
                    'floor_level': p.floor_level or '',
                    'zone': p.zone or '',
                    'discipline': p.discipline or '',
                    'trade': p.trade or '',
                    'drawing_number': p.drawing_number or '',
                    'main_contractor': p.main_contractor or '',
                    'author': p.author or '',
                    'metadata_confidence': float(p.metadata_confidence),
                    'chunk_sequence': int(p.chunk_sequence),
                    'total_chunks': int(p.total_chunks),
                    'content_hash': p.content_hash,
                    'preprocessed_text': p.preprocessed_text,
                } for p in payloads
            ],
            "embeddings": embeddings
        }
        
        try:
            res = requests.post(f"{INTERNAL_API_BASE}upsert/", json=data, timeout=30)
            if res.status_code == 200:
                return res.json().get("count", 0)
            logger.error(f"Internal upsert failed: {res.text}")
            return 0
        except Exception as e:
            logger.error(f"Internal upsert error: {e}")
            return 0

    def get_existing_hashes(self, document_id: str) -> dict[str, str]:
        try:
            res = requests.post(f"{INTERNAL_API_BASE}get_hashes/", json={"document_id": document_id}, timeout=30)
            if res.status_code == 200:
                return res.json()
            return {}
        except Exception as e:
            logger.error(f"Internal get_hashes error: {e}")
            return {}

    def delete_chunks_for_document(self, document_id: str) -> int:
        try:
            res = requests.post(f"{INTERNAL_API_BASE}delete/", json={"document_id": document_id}, timeout=30)
            if res.status_code == 200:
                return res.json().get("deleted", 0)
            return 0
        except Exception as e:
            logger.error(f"Internal delete error: {e}")
            return 0

    def get_collection_stats(self) -> Dict[str, Any]:
        # Proxied via the public stat API instead since we need stats
        try:
            res = requests.get('http://127.0.0.1:8000/api/indexing/collection/stats/', timeout=10)
            if res.status_code == 200:
                return res.json()
        except Exception:
            pass
            
        return {
            'total_vectors': 0,
            'gemini_vectors': 0,
            'nomic_vectors': 0,
            'persist_directory': self.persist_directory,
        }
