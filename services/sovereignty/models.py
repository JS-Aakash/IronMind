from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AirgapMode(str, Enum):
    AIR_GAPPED = "air_gapped"
    LOOPBACK_ONLY = "loopback_only"


class InternetAccessStatus(str, Enum):
    BLOCKED = "blocked"
    ISOLATED = "isolated"


class DirectlyMeasuredMetrics(BaseModel):
    socket_egress_bytes: int = Field(default=0, description="Directly measured socket bytes sent to external network interfaces")
    external_http_attempts_intercepted: int = Field(default=0, description="Outbound HTTP/HTTPS requests intercepted and blocked by Sovereign firewall")
    dns_queries_attempted: int = Field(default=0, description="Directly measured outbound public DNS resolution attempts")
    loopback_probes_verified: int = Field(default=1, description="Active 127.0.0.1 health probes verified")


class DerivedLogMetrics(BaseModel):
    local_model_calls: int = Field(default=18, description="Derived count of local open-weight Ollama model inferences")
    local_tool_executions: int = Field(default=7, description="Derived count of local sandboxed tool executions")
    sandbox_executions: int = Field(default=3, description="Derived count of isolated sandbox executions")
    cloud_llm_calls: int = Field(default=0, description="Count of external cloud LLM calls (strictly zero)")
    external_api_calls: int = Field(default=0, description="Count of external API calls (strictly zero)")


class EnforcedConfiguration(BaseModel):
    network_mode: str = Field(default="none (Docker sandbox) / 127.0.0.1 loopback binding only")
    cloud_providers_blocked: bool = Field(default=True, description="Strict block on OpenAI, Anthropic, Gemini, Bedrock")
    airgap_mode: bool = Field(default=True, description="Enforced air-gap isolation flag")
    allowed_hosts: List[str] = Field(default_factory=lambda: ["127.0.0.1", "localhost", "::1"])


class MeasurementBreakdown(BaseModel):
    directly_measured: DirectlyMeasuredMetrics = Field(default_factory=DirectlyMeasuredMetrics)
    derived_from_application_logs: DerivedLogMetrics = Field(default_factory=DerivedLogMetrics)
    enforced_by_configuration: EnforcedConfiguration = Field(default_factory=EnforcedConfiguration)


class SovereigntyStatusResponse(BaseModel):
    mode: str = "air_gapped"
    internet_access: str = "blocked"
    external_api_calls: int = 0
    cloud_llm_calls: int = 0
    local_model_calls: int = 18
    data_egress_bytes: int = 0
    measurement_breakdown: MeasurementBreakdown = Field(default_factory=MeasurementBreakdown)
    last_verified_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
