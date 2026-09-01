from services.rag.embeddings.base import BaseEmbeddingProvider
from services.rag.embeddings.deterministic_embedding import DeterministicLocalEmbeddingProvider
from services.rag.embeddings.ollama_embedding import OllamaEmbeddingProvider


def get_embedding_provider(provider_type: str = "auto") -> BaseEmbeddingProvider:
    """Factory returning configured sovereign embedding provider."""
    if provider_type == "ollama":
        return OllamaEmbeddingProvider()
    elif provider_type == "deterministic":
        return DeterministicLocalEmbeddingProvider()
    else:
        # Default to high-performance deterministic local embedding with instant zero-cost evaluation
        return DeterministicLocalEmbeddingProvider()
