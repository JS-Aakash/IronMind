import base64
import json
import logging
import re
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional
import httpx

from apps.backend.app.core.errors import ModelInferenceError
from packages.shared.models.enums import ModelStatus
from services.model_gateway.models import (
    GenerationResponse,
    ModelHealthResponse,
    StreamChunk,
)
from services.model_gateway.providers.base import ModelProvider

logger = logging.getLogger(__name__)


class OllamaProvider(ModelProvider):
    """Local inference provider wrapping the self-hosted Ollama runtime."""

    def __init__(self, base_url: str = "http://127.0.0.1:11434", timeout_seconds: float = 120.0, connect_timeout: float = 2.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.connect_timeout = connect_timeout

    @property
    def _timeout_config(self) -> httpx.Timeout:
        return httpx.Timeout(self.timeout_seconds, connect=self.connect_timeout)

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _encode_image(self, image_input: str) -> str:
        """Convert image filepath or existing base64 string to standard base64."""
        # If it is already a base64 string
        if image_input.startswith("data:image") or len(image_input) > 256 and not Path(image_input).exists():
            if "," in image_input:
                return image_input.split(",", 1)[1]
            return image_input

        path = Path(image_input)
        if path.exists() and path.is_file():
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        
        return image_input

    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse valid JSON from raw text or markdown codeblocks."""
        # Try direct parse
        try:
            return json.loads(text.strip())
        except Exception:
            pass

        # Try extract from markdown ```json ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            try:
                return json.loads(match.group(1).strip())
            except Exception:
                pass

        # Try find first '{' and last '}'
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                pass

        return None

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
        start_time = time.perf_counter()
        url = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": -1,
            "think": kwargs.get("think", False),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens if max_tokens is not None else 4096,
                "num_thread": 8,
                "repeat_penalty": 1.1,
                "top_p": 0.9,
                "top_k": 40,
            },
        }

        if "0.6b" in model.lower():
            payload["options"]["num_gpu"] = 0
            payload["options"]["num_ctx"] = 4096
        else:
            payload["options"].setdefault("num_ctx", 8192)

        if system_prompt:
            payload["system"] = system_prompt
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences

        try:
            async with httpx.AsyncClient(timeout=self._timeout_config) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ModelInferenceError(
                        f"Ollama inference failed with status {response.status_code}: {response.text}",
                        details={"status_code": response.status_code, "model": model},
                    )
                data = response.json()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raw_response = data.get("response", "")
            thinking_text = data.get("thinking")
            # If response is empty (e.g. reasoning token limit reached before final block), use thinking as fallback
            text_output = raw_response if raw_response.strip() else (thinking_text or "")
            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            return GenerationResponse(
                model=model,
                provider=self.provider_name,
                text=text_output,
                thinking=thinking_text,
                total_tokens=prompt_eval_count + eval_count,
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                latency_ms=latency_ms,
                finish_reason=data.get("done_reason") or ("stop" if data.get("done", False) else "unknown"),
            )

        except httpx.ConnectError as e:
            raise ModelInferenceError(
                f"Cannot connect to local Ollama server at {self.base_url}. Ensure Ollama is running.",
                details={"base_url": self.base_url, "error": str(e)},
            )
        except httpx.TimeoutException as e:
            raise ModelInferenceError(
                f"Ollama inference timed out after {self.timeout_seconds}s.",
                details={"timeout": self.timeout_seconds, "error": str(e)},
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
        start_time = time.perf_counter()
        url = f"{self.base_url}/api/generate"

        system_instruction = system_prompt or ""
        if schema_definition:
            system_instruction += f"\nYou MUST return response strictly adhering to JSON schema:\n{json.dumps(schema_definition)}"
        else:
            system_instruction += "\nYou MUST return valid JSON without additional conversational text."

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "system": system_instruction.strip(),
            "format": "json",
            "stream": False,
            "keep_alive": -1,
            "think": kwargs.get("think", False),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens if max_tokens is not None else 4096,
                "num_thread": 8,
                "repeat_penalty": 1.1,
                "top_p": 0.9,
            },
        }
        if "0.6b" in model.lower():
            payload["options"]["num_gpu"] = 0
            payload["options"]["num_ctx"] = 4096
        else:
            payload["options"].setdefault("num_ctx", 8192)

        try:
            async with httpx.AsyncClient(timeout=self._timeout_config) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ModelInferenceError(
                        f"Ollama structured generation failed: {response.text}",
                        details={"status_code": response.status_code, "model": model},
                    )
                data = response.json()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raw_text = data.get("response", "")
            thinking_text = data.get("thinking")
            if not raw_text.strip() and thinking_text:
                raw_text = thinking_text
            parsed_data = self._extract_json_from_text(raw_text)

            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            return GenerationResponse(
                model=model,
                provider=self.provider_name,
                text=raw_text,
                thinking=thinking_text,
                structured_data=parsed_data,
                total_tokens=prompt_eval_count + eval_count,
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                latency_ms=latency_ms,
                finish_reason="stop",
            )

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ModelInferenceError(
                f"Ollama connection error: {str(e)}",
                details={"base_url": self.base_url, "error": str(e)},
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
        start_time = time.perf_counter()
        url = f"{self.base_url}/api/generate"

        encoded_images = [self._encode_image(img) for img in images]

        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "images": encoded_images,
            "stream": False,
            "keep_alive": -1,
            "think": kwargs.get("think", False),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens if max_tokens is not None else 4096,
                "num_thread": 8,
                "repeat_penalty": 1.1,
                "top_p": 0.9,
            },
        }
        payload["options"].setdefault("num_ctx", 8192)
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=self._timeout_config) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise ModelInferenceError(
                        f"Ollama vision analysis failed: {response.text}",
                        details={"status_code": response.status_code, "model": model},
                    )
                data = response.json()

            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            raw_text = data.get("response", "")
            thinking_text = data.get("thinking")
            if not raw_text.strip() and thinking_text:
                raw_text = thinking_text
            parsed_data = self._extract_json_from_text(raw_text)

            prompt_eval_count = data.get("prompt_eval_count", 0)
            eval_count = data.get("eval_count", 0)

            return GenerationResponse(
                model=model,
                provider=self.provider_name,
                text=raw_text,
                thinking=thinking_text,
                structured_data=parsed_data,
                total_tokens=prompt_eval_count + eval_count,
                prompt_tokens=prompt_eval_count,
                completion_tokens=eval_count,
                latency_ms=latency_ms,
                finish_reason="stop",
            )
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ModelInferenceError(
                f"Ollama vision connection error: {str(e)}",
                details={"base_url": self.base_url, "error": str(e)},
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
        url = f"{self.base_url}/api/generate"
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": True,
            "keep_alive": -1,
            "think": kwargs.get("think", False),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens if max_tokens is not None else 4096,
                "num_thread": 8,
                "repeat_penalty": 1.1,
                "top_p": 0.9,
            },
        }
        if "0.6b" in model.lower():
            payload["options"]["num_gpu"] = 0
            payload["options"]["num_ctx"] = 4096
        else:
            payload["options"].setdefault("num_ctx", 8192)

        if system_prompt:
            payload["system"] = system_prompt

        images = kwargs.get("images") or kwargs.get("image_base64")
        if images:
            if isinstance(images, str):
                images = [images]
            encoded_images = [self._encode_image(img) for img in images if img]
            if encoded_images:
                payload["images"] = encoded_images

        accumulated_len = 0
        try:
            async with httpx.AsyncClient(timeout=self._timeout_config) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        raise ModelInferenceError(
                            f"Ollama stream error: HTTP {response.status_code}",
                            details={"status_code": response.status_code},
                        )
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk_data = json.loads(line)
                            chunk_text = chunk_data.get("response", "")
                            if not chunk_text and kwargs.get("think", False) and chunk_data.get("thinking"):
                                chunk_text = chunk_data.get("thinking", "")
                            is_done = chunk_data.get("done", False)
                            accumulated_len += len(chunk_text)
                            yield StreamChunk(
                                text=chunk_text,
                                is_done=is_done,
                                finish_reason="stop" if is_done else None,
                                accumulated_length=accumulated_len,
                            )
                        except json.JSONDecodeError:
                            continue
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            raise ModelInferenceError(
                f"Ollama streaming connection error: {str(e)}",
                details={"base_url": self.base_url, "error": str(e)},
            )

    async def check_health(self, model: str) -> ModelHealthResponse:
        start_time = time.perf_counter()
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                if res.status_code == 200:
                    models_list = res.json().get("models", [])
                    available_names = [m.get("name") for m in models_list]
                    is_available = any(model in name for name in available_names)
                    return ModelHealthResponse(
                        name=model,
                        provider=self.provider_name,
                        available=is_available,
                        status=ModelStatus.LOADED if is_available else ModelStatus.STANDBY,
                        latency_ms=latency_ms,
                        details={"installed_models": available_names, "matched": is_available},
                    )
                return ModelHealthResponse(
                    name=model,
                    provider=self.provider_name,
                    available=False,
                    status=ModelStatus.ERROR,
                    latency_ms=latency_ms,
                    details={"error": f"HTTP {res.status_code}"},
                )
        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return ModelHealthResponse(
                name=model,
                provider=self.provider_name,
                available=False,
                status=ModelStatus.UNLOADED,
                latency_ms=latency_ms,
                details={"error": str(e), "message": "Ollama service is not reachable on localhost."},
            )

    async def list_available_models(self) -> List[str]:
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    return [m.get("name", "") for m in res.json().get("models", [])]
        except Exception:
            pass
        return []
