from abc import ABC, abstractmethod
from typing import BinaryIO

class BaseStorage(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def save(self, name: str, content: BinaryIO) -> str:
        """Save a file and return its storage path or URI."""
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a file exists."""
        pass
        
    @abstractmethod
    def get_url(self, name: str) -> str:
        """Get the access URL for the file."""
        pass
