from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract sovereign on-premise embedding provider."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for a single text chunk."""
        pass

    @abstractmethod
    def embed_text_sync(self, text: str) -> List[float]:
        """Synchronously generate embedding vector."""
        pass

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of text chunks."""
        return [await self.embed_text(t) for t in texts]

    def embed_batch_sync(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text_sync(t) for t in texts]
