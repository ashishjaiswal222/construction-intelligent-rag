import os
from typing import BinaryIO
from django.conf import settings
from .base import BaseStorage

class LocalStorage(BaseStorage):
    """Local file system storage backend."""
    
    def __init__(self):
        self.upload_dir = os.path.join(settings.BASE_DIR, 'uploads')
        os.makedirs(self.upload_dir, exist_ok=True)
        
    def save(self, name: str, content: BinaryIO) -> str:
        """Saves file to local disk and returns absolute path."""
        storage_path = os.path.join(self.upload_dir, name)
        
        with open(storage_path, 'wb+') as destination:
            for chunk in content.chunks() if hasattr(content, 'chunks') else [content.read()]:
                destination.write(chunk)
                
        return storage_path

    def exists(self, name: str) -> bool:
        return os.path.exists(os.path.join(self.upload_dir, name))
        
    def get_url(self, name: str) -> str:
        # For local dev, we return the path. In prod, this would be a media URL.
        return os.path.join(self.upload_dir, name)
