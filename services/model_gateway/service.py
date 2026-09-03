import logging
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx
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

    @staticmethod
    def _model_matches(target_id: str, running_tag: str) -> bool:
        """Accurately match target model ID against Ollama running tag.
        Guarantees that qwen3:0.6b never matches qwen3:8b or vice versa.
        """
        t = target_id.lower().strip().replace("-", "")
        r = running_tag.lower().strip().replace("-", "")

        if t == r:
            return True

        if ":" in t and ":" in r:
            tb, tv = t.split(":", 1)
            rb, rv = r.split(":", 1)
            return tb == rb and tv == rv

        return False

    async def get_running_ollama_models(self) -> List[Dict[str, Any]]:
        """Fetch running models directly from local Ollama runtime (/api/ps)."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.ollama_base_url}/api/ps")
                if res.status_code == 200:
                    data = res.json()
                    return data.get("models", [])
        except Exception as e:
            logger.debug("Could not query Ollama /api/ps: %s", str(e))
        return []

    async def get_models_status(self) -> List[Dict[str, Any]]:
        """Get real-time operational status and memory residency for all 4 primary industrial models."""
        running_models = await self.get_running_ollama_models()

        models_meta = [
            ("qwen3:0.6b", "Qwen3:0.6B - Router", "Fast AI Task Classifier", ModelRole.ROUTING, 450),
            ("qwen3:8b", "Qwen3:8B - Reasoning", "Industrial Reasoning & Planning", ModelRole.REASONING, 5000),
            ("qwen2.5-coder:7b", "Qwen2.5-Coder:7B - Coding", "Python & Sandbox Verification", ModelRole.CODING, 4500),
            ("qwen2.5vl:7b", "Qwen2.5-VL:7B - Vision", "Multimodal & Engineering Drawings", ModelRole.VISION, 5500),
        ]

        result = []
        for model_id, display_name, description, role, est_vram in models_meta:
            m_info = None
            for m in running_models:
                running_name = m.get("name", "")
                if self._model_matches(model_id, running_name):
                    m_info = m
                    break

            is_warm = m_info is not None
            vram_mb = int(m_info.get("size_vram", 0) / (1024 * 1024)) if (m_info and m_info.get("size_vram")) else 0

            result.append({
                "id": model_id,
                "name": model_id,
                "display_name": display_name,
                "description": description,
                "role": role.value if hasattr(role, "value") else str(role),
                "status": "LOADED • WARM" if is_warm else "UNLOADED",
                "is_warm": is_warm,
                "vram_usage_mb": vram_mb if vram_mb > 0 else (est_vram if is_warm else 0),
                "expires_at": m_info.get("expires_at") if m_info else None,
            })

        return result

    async def load_model(self, model_id: str) -> ModelInfo:
        """Preload model into local VRAM using Ollama keep_alive=-1 to eliminate cold start."""
        model = self.registry.get_model(model_id)
        target_name = model.name if model else model_id

        # Call Ollama /api/generate with keep_alive=-1 (indefinite warm residency)
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                res = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={"model": target_name, "keep_alive": -1},
                )
                if res.status_code != 200:
                    logger.warning("Ollama pre-warm returned HTTP %s: %s", res.status_code, res.text)
        except Exception as e:
            logger.error("Failed to warm-load model '%s' in Ollama: %s", target_name, str(e))

        if model:
            model.enabled = True

        running_models = await self.get_running_ollama_models()
        is_warm = any(self._model_matches(target_name, m.get("name", "")) for m in running_models)
        actual_vram = model.vram_estimate_mb if model else 4500
        for m in running_models:
            if self._model_matches(target_name, m.get("name", "")):
                actual_vram = int(m.get("size_vram", 0) / (1024 * 1024))
                break

        return ModelInfo(
            id=model.name if model else target_name,
            name=model.display_name if model else target_name,
            role=model.role if model else ModelRole.REASONING,
            version=model.name if model else target_name,
            provider="ollama",
            capabilities=model.capabilities if model else ["inference"],
            vram_usage_mb=int(actual_vram),
            context_length=model.context_length if model else 8192,
            status=ModelStatus.LOADED,
        )

    async def unload_model(self, model_id: str) -> ModelInfo:
        """Explicitly unload model from local VRAM using Ollama keep_alive=0."""
        model = self.registry.get_model(model_id)
        target_name = model.name if model else model_id

        # Call Ollama /api/generate with keep_alive=0 (immediate release)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={"model": target_name, "keep_alive": 0},
                )
        except Exception as e:
            logger.warning("Error releasing model '%s' from Ollama: %s", target_name, str(e))

        if model:
            model.enabled = False

        return ModelInfo(
            id=model.name if model else target_name,
            name=model.display_name if model else target_name,
            role=model.role if model else ModelRole.REASONING,
            version=model.name if model else target_name,
            provider="ollama",
            capabilities=model.capabilities if model else ["inference"],
            vram_usage_mb=0,
            context_length=model.context_length if model else 8192,
            status=ModelStatus.UNLOADED,
        )


# Backward compatibility alias
ModelGatewayService = ModelService
