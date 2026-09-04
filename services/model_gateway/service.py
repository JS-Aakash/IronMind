import asyncio
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
        self._router_pinned: bool = True
        self._active_gpu_model: Optional[str] = None
        self._loading_model_id: Optional[str] = None
        self._loading_lock = asyncio.Lock()

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
        model_name = self.registry.get_model_for_role(role)
        m = self.registry.get_model(model_name)
        if not m:
            matching = self.registry.find_by_role(role)
            m = matching[0] if matching else None
        if not m:
            matching = self.registry.list_models(enabled_only=True)
            m = matching[0] if matching else None
        if not m:
            return None
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

    async def get_installed_ollama_models(self) -> List[str]:
        """Fetch all downloaded models in local Ollama instance."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.ollama_base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                    if models:
                        return models
        except Exception as e:
            logger.debug("Could not query Ollama /api/tags: %s", e)

        return ["qwen3:0.6b", "qwen3:8b", "qwen3:14b", "qwen2.5-coder:7b", "qwen2.5-coder:14b", "qwen2.5vl:7b"]

    async def get_models_status(self) -> List[Dict[str, Any]]:
        """Get real-time operational status and memory residency for all 4 primary industrial models."""
        running_models = await self.get_running_ollama_models()

        role_configs = [
            ("routing", ModelRole.ROUTING, "Router", "Fast AI Task Classifier", 450),
            ("reasoning", ModelRole.REASONING, "Reasoning", "Industrial Reasoning & Planning", 5000),
            ("coding", ModelRole.CODING, "Coding", "Python & Sandbox Verification", 4500),
            ("vision", ModelRole.VISION, "Vision", "Multimodal & Engineering Drawings", 5500),
        ]

        result = []
        for role_key, role_enum, role_title, default_desc, default_vram in role_configs:
            model_id = self.registry.get_model_for_role(role_enum)
            model_def = self.registry.get_model(model_id)

            m_info = None
            for m in running_models:
                running_name = m.get("name", "")
                if self._model_matches(model_id, running_name):
                    m_info = m
                    break

            is_warm = m_info is not None
            is_loading = self._loading_model_id is not None and self._model_matches(self._loading_model_id, model_id)
            vram_mb = int(m_info.get("size_vram", 0) / (1024 * 1024)) if (m_info and m_info.get("size_vram")) else 0

            status_str = "LOADING" if is_loading else ("LOADED • WARM" if is_warm else "UNLOADED")
            display_name = f"{model_id} - {role_title}"
            desc = model_def.description if model_def else default_desc
            est_vram = model_def.vram_estimate_mb if model_def else default_vram

            result.append({
                "id": model_id,
                "name": model_id,
                "display_name": display_name,
                "description": desc,
                "role": role_key,
                "role_title": role_title,
                "status": status_str,
                "is_warm": is_warm or is_loading,
                "is_loading": is_loading,
                "vram_usage_mb": vram_mb if vram_mb > 0 else (est_vram if (is_warm or is_loading) else 0),
                "expires_at": m_info.get("expires_at") if m_info else None,
            })

        return result

    async def load_model(self, model_id: str) -> ModelInfo:
        """Preload model into memory using Ollama keep_alive=-1 to eliminate cold start."""
        async with self._loading_lock:
            model = self.registry.get_model(model_id)
            target_name = model.name if model else model_id
            self._loading_model_id = target_name

            try:
                router_tag = self.registry.get_model_for_role(ModelRole.ROUTING)
                is_router = (
                    self._model_matches(router_tag, target_name)
                    or "0.6b" in target_name.lower()
                    or "0.5b" in target_name.lower()
                )

                if is_router:
                    # Router runs on CPU (0 bytes GPU VRAM)
                    load_payload: Dict[str, Any] = {
                        "model": target_name,
                        "prompt": "",
                        "keep_alive": -1,
                        "options": {"num_gpu": 0, "num_ctx": 2048},
                    }
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        await client.post(
                            f"{self.ollama_base_url}/api/generate",
                            json=load_payload,
                        )
                    self._router_pinned = True
                else:
                    # Specialist GPU model
                    load_payload = {
                        "model": target_name,
                        "prompt": "",
                        "keep_alive": -1,
                        "options": {"num_ctx": 2048},
                    }
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        res = await client.post(
                            f"{self.ollama_base_url}/api/generate",
                            json=load_payload,
                        )
                        if res.status_code != 200:
                            logger.warning("Ollama load returned HTTP %s: %s", res.status_code, res.text)
                    self._active_gpu_model = target_name

                    # Concurrently reinforce router model on CPU so both stay warm
                    if self._router_pinned:
                        router_payload: Dict[str, Any] = {
                            "model": router_tag,
                            "prompt": "",
                            "keep_alive": -1,
                            "options": {"num_gpu": 0, "num_ctx": 2048},
                        }
                        try:
                            async with httpx.AsyncClient(timeout=30.0) as client:
                                await client.post(f"{self.ollama_base_url}/api/generate", json=router_payload)
                        except Exception as ex:
                            logger.debug("Could not reinforce router model: %s", ex)

                if model:
                    model.enabled = True

                running_models = await self.get_running_ollama_models()
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
            finally:
                self._loading_model_id = None

    async def unload_model(self, model_id: str) -> ModelInfo:
        """Explicitly unload model from memory using Ollama keep_alive=0."""
        async with self._loading_lock:
            model = self.registry.get_model(model_id)
            target_name = model.name if model else model_id
            self._loading_model_id = target_name

            try:
                is_router = "0.6b" in target_name.lower()
                if is_router:
                    self._router_pinned = False
                elif self._active_gpu_model and self._model_matches(self._active_gpu_model, target_name):
                    self._active_gpu_model = None

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
            finally:
                self._loading_model_id = None


# Backward compatibility alias
ModelGatewayService = ModelService
