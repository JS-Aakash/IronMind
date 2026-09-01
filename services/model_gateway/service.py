import logging
from typing import AsyncIterator, Dict, List, Optional
from apps.backend.app.core.config import settings
from apps.backend.app.core.errors import ModelInferenceError, ResourceNotFoundError
from packages.shared.models.enums import ModelRole, ModelStatus
from packages.shared.models.schemas import ModelInfo
from services.model_gateway.models import (
    GenerationRequest,
    GenerationResponse,
    ModelDefinition,
    ModelHealthResponse,
    StreamChunk,
)
from services.model_gateway.providers.base import ModelProvider
from services.model_gateway.providers.mock import MockProvider
from services.model_gateway.providers.ollama import OllamaProvider
from services.model_gateway.registry import ModelRegistry

logger = logging.getLogger(__name__)


class ModelService:
    """Unified Gateway Service for all local open-weight model inferences in IronMind."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        default_provider: Optional[str] = None,
        ollama_base_url: Optional[str] = None,
    ):
        self.registry = registry or ModelRegistry()
        self.default_provider_name = default_provider or settings.LOCAL_INFERENCE_PROVIDER
        self.ollama_base_url = ollama_base_url or settings.OLLAMA_BASE_URL

        # Register provider instances
        self._providers: Dict[str, ModelProvider] = {
            "ollama": OllamaProvider(base_url=self.ollama_base_url),
            "mock": MockProvider(provider_name="mock"),
        }

    def register_provider(self, provider: ModelProvider) -> None:
        """Register a new inference provider (e.g. vLLM, TensorRT-LLM)."""
        self._providers[provider.provider_name] = provider
        logger.info("Registered inference provider: %s", provider.provider_name)

    def get_provider(self, provider_name: str) -> ModelProvider:
        """Retrieve provider instance by name."""
        if provider_name not in self._providers:
            # Fallback to default or mock
            if self.default_provider_name in self._providers:
                return self._providers[self.default_provider_name]
            return self._providers["mock"]
        return self._providers[provider_name]

    def _resolve_model_and_provider(self, model_name: str) -> tuple[ModelDefinition, ModelProvider]:
        """Resolve model definition and appropriate provider."""
        model_def = self.registry.get_model(model_name)
        if not model_def:
            # If not in registry, create dynamic definition
            model_def = ModelDefinition(
                name=model_name,
                display_name=model_name,
                provider=self.default_provider_name,
                role=ModelRole.REASONING,
                capabilities=["general_text"],
            )

        provider = self.get_provider(model_def.provider)
        return model_def, provider

    async def generate_text(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2048,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> GenerationResponse:
        """Generate text completion through the local model gateway."""
        model_def, provider = self._resolve_model_and_provider(model)
        logger.info("Dispatching text generation to [%s] via provider [%s]", model_def.name, provider.provider_name)
        return await provider.generate_text(
            model=model_def.name,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            stop_sequences=stop_sequences,
            **kwargs,
        )

    async def generate_structured(
        self,
        model: str,
        prompt: str,
        schema_definition: Optional[Dict] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = 2048,
        **kwargs,
    ) -> GenerationResponse:
        """Generate structured JSON adhering to requested schema."""
        model_def, provider = self._resolve_model_and_provider(model)
        logger.info("Dispatching structured generation to [%s] via [%s]", model_def.name, provider.provider_name)
        return await provider.generate_structured(
            model=model_def.name,
            prompt=prompt,
            schema_definition=schema_definition,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def analyze_image(
        self,
        model: str,
        prompt: str,
        images: Optional[List[str]] = None,
        image_base64: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = 2048,
        **kwargs,
    ) -> GenerationResponse:
        """Multimodal visual inspection of drawings, photographs, people, equipment, or scanned reports."""
        imgs = images if images is not None else ([image_base64] if image_base64 else [])
        model_def, provider = self._resolve_model_and_provider(model)
        logger.info("Dispatching multimodal vision analysis to [%s] with %d image(s)", model_def.name, len(imgs))
        return await provider.analyze_image(
            model=model_def.name,
            prompt=prompt,
            images=imgs,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    async def stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = 2048,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        """Stream generated token chunks."""
        model_def, provider = self._resolve_model_and_provider(model)
        logger.info("Initiating stream on [%s] via [%s]", model_def.name, provider.provider_name)
        async for chunk in provider.stream(
            model=model_def.name,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        ):
            yield chunk

    async def check_model_health(self, model_name: str) -> ModelHealthResponse:
        """Check status and reachability of a registered model."""
        model_def, provider = self._resolve_model_and_provider(model_name)
        return await provider.check_health(model_def.name)

    def list_models(self) -> List[ModelInfo]:
        """List all models in shared ModelInfo format for UI and API consumption."""
        registered = self.registry.list_models(enabled_only=False)
        output: List[ModelInfo] = []
        for m in registered:
            output.append(
                ModelInfo(
                    id=m.name,
                    name=m.display_name,
                    role=m.role,
                    version=m.name,
                    provider=m.provider,
                    capabilities=m.capabilities,
                    vram_usage_mb=m.vram_estimate_mb,
                    context_length=m.context_length,
                    status=ModelStatus.LOADED if m.enabled else ModelStatus.UNLOADED,
                )
            )
        return output

    def get_model_definition(self, name: str) -> Optional[ModelDefinition]:
        """Get model definition from registry."""
        return self.registry.get_model(name)

    def route_task_to_model(self, role: ModelRole) -> Optional[ModelInfo]:
        """Find best matching model for capability role."""
        matching = self.registry.find_by_role(role)
        if not matching:
            # Fallback to first enabled model
            matching = self.registry.list_models(enabled_only=True)
        if not matching:
            return None
        m = matching[0]
        return ModelInfo(
            id=m.name,
            name=m.display_name,
            role=m.role,
            version=m.name,
            provider=m.provider,
            capabilities=m.capabilities,
            vram_usage_mb=m.vram_estimate_mb,
            context_length=m.context_length,
            status=ModelStatus.LOADED,
        )

    def load_model(self, model_id: str) -> ModelInfo:
        """Enable / mark model as loaded."""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not registered.")
        model.enabled = True
        return ModelInfo(
            id=model.name,
            name=model.display_name,
            role=model.role,
            version=model.name,
            provider=model.provider,
            capabilities=model.capabilities,
            vram_usage_mb=model.vram_estimate_mb,
            context_length=model.context_length,
            status=ModelStatus.LOADED,
        )

    def unload_model(self, model_id: str) -> ModelInfo:
        """Disable / mark model as unloaded."""
        model = self.registry.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not registered.")
        model.enabled = False
        return ModelInfo(
            id=model.name,
            name=model.display_name,
            role=model.role,
            version=model.name,
            provider=model.provider,
            capabilities=model.capabilities,
            vram_usage_mb=0,
            context_length=model.context_length,
            status=ModelStatus.UNLOADED,
        )


# Backward compatibility alias
ModelGatewayService = ModelService
