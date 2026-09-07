from .base import BaseStorage
from .local_storage import LocalStorage

# Simple factory pattern to get default storage
def get_storage() -> BaseStorage:
    # In the future, this can read settings.STORAGE_BACKEND to return S3Storage, etc.
    return LocalStorage()

__all__ = ['BaseStorage', 'LocalStorage', 'get_storage']
