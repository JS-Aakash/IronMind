import asyncio
from typing import AsyncIterator, Dict, List, Optional
from packages.shared.models.enums import ModelStatus
from services.model_gateway.models import (
    GenerationResponse,
    ModelHealthResponse,
    StreamChunk,
)
from services.model_gateway.providers.base import ModelProvider


class MockProvider(ModelProvider):
    """Deterministic Mock Provider for robust unit testing and fallback test simulations."""

    def __init__(self, provider_name: str = "mock"):
        self._provider_name = provider_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

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
        if "coder" in model or "code" in prompt.lower() or "python" in prompt.lower():
            mock_text = (
                "```python\n"
                "def calculate_metrics(val: float = 10.0) -> float:\n"
                "    return val * 1.5\n\n"
                "assert calculate_metrics(10.0) == 15.0\n"
                "print('All calculation assertions passed.')\n"
                "```"
            )
        else:
            mock_text = f"[MockResponse from {model}]: Reasoning completed for prompt '{prompt[:30]}...'"

        return GenerationResponse(
            model=model,
            provider=self.provider_name,
            text=mock_text,
            total_tokens=42,
            prompt_tokens=18,
            completion_tokens=24,
            latency_ms=12.5,
            finish_reason="stop",
        )

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
        mock_data = {
            "status": "success",
            "task": "simulated_analysis",
            "model_used": model,
            "findings": ["Finding 1: Normal vibration level", "Finding 2: Pressure within API limit"],
            "confidence": 0.95,
        }
        return GenerationResponse(
            model=model,
            provider=self.provider_name,
            text=str(mock_data),
            structured_data=mock_data,
            total_tokens=60,
            prompt_tokens=25,
            completion_tokens=35,
            latency_ms=15.0,
            finish_reason="stop",
        )

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
        mock_data = {
            "visual_elements_detected": ["Centrifugal Pump P-101", "Pressure Transmitter PT-101", "Flow Control Valve FV-102"],
            "image_count": len(images),
            "model": model,
        }
        return GenerationResponse(
            model=model,
            provider=self.provider_name,
            text=f"[MockVision from {model}]: Identified 3 industrial equipment units in provided image(s).",
            structured_data=mock_data,
            total_tokens=85,
            prompt_tokens=40,
            completion_tokens=45,
            latency_ms=22.0,
            finish_reason="stop",
        )

    async def stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> AsyncIterator[StreamChunk]:
        tokens = ["[MockStream", " from ", model, "]: ", "Executing ", "step-by-step ", "analysis."]
        acc = 0
        for i, token in enumerate(tokens):
            await asyncio.sleep(0.01)
            acc += len(token)
            is_last = i == len(tokens) - 1
            yield StreamChunk(
                text=token,
                is_done=is_last,
                finish_reason="stop" if is_last else None,
                accumulated_length=acc,
            )

    async def check_health(self, model: str) -> ModelHealthResponse:
        return ModelHealthResponse(
            name=model,
            provider=self.provider_name,
            available=True,
            status=ModelStatus.LOADED,
            latency_ms=5.0,
            details={"mode": "mock_test_mode", "active": True},
        )

    async def list_available_models(self) -> List[str]:
        return ["qwen3:8b", "qwen2.5-coder:7b", "qwen2.5vl:7b"]
