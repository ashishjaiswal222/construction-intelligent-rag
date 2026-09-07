import os
import threading
from qdrant_client import QdrantClient

class QdrantManager:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get_client(cls, persist_directory=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    if persist_directory is None:
                        persist_directory = os.environ.get('QDRANT_PERSIST_DIR', './construction_qdrant_db')
                    # We use prefer_grpc=True, but local Qdrant ignores it.
                    cls._instance = QdrantClient(path=persist_directory, prefer_grpc=True)
        return cls._instance
