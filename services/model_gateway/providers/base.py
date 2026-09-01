from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, List, Optional
from services.model_gateway.models import (
    GenerationRequest,
    GenerationResponse,
    ModelHealthResponse,
    StreamChunk,
)


class ModelProvider(ABC):
    """Abstract Base Class for local on-premise model inference providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'ollama', 'vllm', 'mock')."""
        pass

    @abstractmethod
    async def generate_text(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> GenerationResponse:
        """Generate text completion from a prompt."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        model: str,
        prompt: str,
        schema_definition: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> GenerationResponse:
        """Generate validated structured JSON output from a prompt."""
        pass

    @abstractmethod
    async def analyze_image(
        self,
        model: str,
        prompt: str,
        images: List[str],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> GenerationResponse:
        """Perform multimodal visual reasoning on images or drawings."""
        pass

    @abstractmethod
    async def stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream token chunks asynchronously."""
        pass

    @abstractmethod
    async def check_health(self, model: str) -> ModelHealthResponse:
        """Check local model availability and readiness."""
        pass

    @abstractmethod
    async def list_available_models(self) -> List[str]:
        """List model tags available on this local provider instance."""
        pass
