from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Tuple
from services.rag.models import DocumentChunk


class BaseVectorStore(ABC):
    """Abstract sovereign on-premise vector store."""

    @abstractmethod
    def add_chunks_sync(self, chunks: List[DocumentChunk]) -> None:
        """Synchronously insert or update chunks with dense embedding vectors."""
        pass

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        self.add_chunks_sync(chunks)

    @abstractmethod
    def search_sync(
        self,
        query_vector: List[float],
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        """Synchronously search top-k most similar document chunks."""
        pass

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 3,
        threshold: float = 0.0,
    ) -> List[Tuple[DocumentChunk, float]]:
        return self.search_sync(query_vector, top_k, threshold)

    @abstractmethod
    def count(self) -> int:
        """Get the total number of chunks indexed."""
        pass

    @abstractmethod
    def delete_chunks_by_document(self, document_id: str) -> int:
        """Remove all chunks associated with a specific document ID."""
        pass

    @abstractmethod
    def save(self, path: Path) -> None:
        pass

    @abstractmethod
    def load(self, path: Path) -> None:
        pass
