from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from packages.shared.models.enums import (
    ArtifactType,
    ModelRole,
    ModelStatus,
    SovereigntyStatus,
    TaskStatus,
    TaskType,
)


class TaskRequirement(BaseModel):
    requires_vision: bool = False
    requires_rag: bool = False
    requires_coding: bool = False
    requires_sandbox: bool = False
    requires_reasoning: bool = True
    target_artifact: Optional[ArtifactType] = None


class TaskCreateRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="Task goal or prompt")
    task_type: Optional[TaskType] = None
    uploaded_files: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)


class TaskStep(BaseModel):
    step_id: str
    order: int
    title: str
    description: str
    tool_name: Optional[str] = None
    model_used: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_summary: Optional[str] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    goal: str
    status: TaskStatus
    task_type: Optional[TaskType] = None
    requirements: Optional[TaskRequirement] = None
    selected_model: Optional[str] = None
    plan: List[TaskStep] = Field(default_factory=list)
    current_step: int = 0
    created_at: datetime
    updated_at: datetime
    artifacts: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class ModelInfo(BaseModel):
    id: str
    name: str
    role: ModelRole
    version: str
    provider: str
    capabilities: List[str] = Field(default_factory=list)
    vram_usage_mb: int = 0
    context_length: int = 8192
    status: ModelStatus = ModelStatus.STANDBY


class KnowledgeDocument(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    category: str
    chunk_count: int = 0
    uploaded_at: datetime
    size_bytes: int


class ArtifactItem(BaseModel):
    id: str
    task_id: str
    filename: str
    artifact_type: ArtifactType
    file_path: str
    size_bytes: int
    created_at: datetime
    models_used: List[str] = Field(default_factory=list)
    source_documents: List[str] = Field(default_factory=list)
    verified: bool = True
    sha256_hash: Optional[str] = None


class SovereigntyMetrics(BaseModel):
    status: SovereigntyStatus = SovereigntyStatus.AIRGAPPED
    external_calls_count: int = 0
    cloud_llm_calls_count: int = 0
    dns_queries_count: int = 0
    egress_bytes: int = 0
    local_inferences_count: int = 0
    local_tool_executions_count: int = 0
    sandbox_runs_count: int = 0
    active_connections: int = 0
    last_audit_timestamp: datetime = Field(default_factory=datetime.utcnow)


class AuditLogEntry(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: str = "INFO"
    event_type: str
    source_service: str
    task_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
