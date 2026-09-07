from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from packages.shared.models.enums import ModelRole, ModelStatus


class ModelDefinition(BaseModel):
    name: str = Field(..., description="Unique model identifier (e.g. qwen3:8b)")
    display_name: str
    provider: str = Field(default="ollama", description="Provider identifier (ollama, vllm, mock)")
    role: ModelRole = Field(default=ModelRole.REASONING)
    capabilities: List[str] = Field(default_factory=list)
    context_length: int = Field(default=32768)
    vram_estimate_mb: int = Field(default=4500)
    enabled: bool = Field(default=True)
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class GenerationRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text")
    system_prompt: Optional[str] = Field(default=None, description="System instructions")
    images: Optional[List[str]] = Field(default=None, description="List of base64 strings or local file paths")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=65536)
    think: Optional[bool] = Field(default=False, description="Enable thinking/reasoning tokens (default False for fast direct generation)")
    json_format: bool = Field(default=False, description="Enforce valid JSON output")
    schema_definition: Optional[Dict[str, Any]] = Field(default=None, description="Target JSON schema to enforce")
    stop_sequences: Optional[List[str]] = Field(default=None)


class GenerationResponse(BaseModel):
    model: str
    provider: str
    text: str
    thinking: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    created_at: datetime = Field(default_factory=datetime.now)


class StreamChunk(BaseModel):
    text: str
    is_done: bool = False
    finish_reason: Optional[str] = None
    accumulated_length: int = 0


class ModelHealthResponse(BaseModel):
    name: str
    provider: str
    available: bool
    status: ModelStatus = ModelStatus.STANDBY
    latency_ms: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime = Field(default_factory=datetime.now)
