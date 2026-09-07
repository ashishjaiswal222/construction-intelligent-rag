import os
import pickle
import logging
from typing import List, Optional, Tuple
from rank_bm25 import BM25Okapi
from document_indexing.schemas.chunk_payload import ChunkPayload

logger = logging.getLogger(__name__)

BM25_INDEX_PATH = os.environ.get('BM25_INDEX_PATH', './bm25_index.pkl')

class BM25IndexService:
    _instance = None

    def __init__(self):
        if BM25IndexService._instance is not None:
            raise Exception("Singleton pattern: use get_instance()")
        self._index: Optional[BM25Okapi] = None
        self._doc_ids: List[str] = [] # Stores chunk_ids
        self._document_ids: List[str] = [] # Stores document_ids parallel to chunk_ids
        self._corpus: List[List[str]] = []
        BM25IndexService._instance = self

    @classmethod
    def get_instance(cls) -> 'BM25IndexService':
        if cls._instance is None:
            cls()
        return cls._instance

    def _tokenize(self, text: str) -> List[str]:
        return text.lower().split() if text else []

    def _rebuild_index(self):
        if self._corpus:
            self._index = BM25Okapi(self._corpus)
        else:
            self._index = None

    def add_documents(self, payloads: List[ChunkPayload]) -> None:
        if not payloads:
            return
            
        for payload in payloads:
            tokenized_text = self._tokenize(payload.preprocessed_text)
            self._corpus.append(tokenized_text)
            self._doc_ids.append(payload.chunk_id)
            self._document_ids.append(str(payload.document_id))
            
        self._rebuild_index()
        self.persist()

    def remove_documents(self, document_id: str) -> int:
        document_id = str(document_id)
        
        new_doc_ids = []
        new_document_ids = []
        new_corpus = []
        removed_count = 0
        
        for i, doc_ref in enumerate(self._document_ids):
            if doc_ref == document_id:
                removed_count += 1
            else:
                new_doc_ids.append(self._doc_ids[i])
                new_document_ids.append(doc_ref)
                new_corpus.append(self._corpus[i])
                
        if removed_count > 0:
            self._doc_ids = new_doc_ids
            self._document_ids = new_document_ids
            self._corpus = new_corpus
            self._rebuild_index()
            self.persist()
            
        return removed_count

    def persist(self) -> None:
        try:
            state = {
                'doc_ids': self._doc_ids,
                'document_ids': self._document_ids,
                'corpus': self._corpus
            }
            with open(BM25_INDEX_PATH, 'wb') as f:
                pickle.dump(state, f)
        except Exception as e:
            logger.error(f"Failed to persist BM25 index: {str(e)}")

    def load(self) -> bool:
        if not os.path.exists(BM25_INDEX_PATH):
            return False
            
        try:
            with open(BM25_INDEX_PATH, 'rb') as f:
                state = pickle.load(f)
                self._doc_ids = state.get('doc_ids', [])
                self._document_ids = state.get('document_ids', [])
                self._corpus = state.get('corpus', [])
                self._rebuild_index()
                return True
        except Exception as e:
            logger.error(f"Failed to load BM25 index: {str(e)}")
            return False
