import logging
from typing import List, Optional
import httpx

from services.rag.embeddings.base import BaseEmbeddingProvider
from services.rag.embeddings.deterministic_embedding import DeterministicLocalEmbeddingProvider

logger = logging.getLogger(__name__)


class OllamaEmbeddingProvider(BaseEmbeddingProvider):
    """Local Ollama-backed embedding provider (supporting BGE-M3, nomic-embed-text, or all-minilm)."""

    def __init__(self, model_name: str = "bge-m3", base_url: str = "http://127.0.0.1:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self._fallback = DeterministicLocalEmbeddingProvider()
        self._dimension = 1024 if "bge-m3" in model_name else 768

    @property
    def provider_name(self) -> str:
        return f"OllamaLocalEmbedding ({self.model_name})"

    @property
    def dimension(self) -> int:
        return self._dimension

    async def embed_text(self, text: str) -> List[float]:
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.model_name, "prompt": text}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    embedding = data.get("embedding")
                    if embedding:
                        self._dimension = len(embedding)
                        return embedding
        except Exception as e:
            logger.debug("Ollama embedding endpoint not available (%s), using local dense fallback.", str(e))

        # Seamless fallback
        return await self._fallback.embed_text(text)
