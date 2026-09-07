from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    TASK_CREATED = "TASK_CREATED"
    TASK_CLASSIFIED = "TASK_CLASSIFIED"
    MODEL_SELECTED = "MODEL_SELECTED"
    MODEL_INFERENCE = "MODEL_INFERENCE"
    TOOL_CALLED = "TOOL_CALLED"
    RAG_RETRIEVAL = "RAG_RETRIEVAL"
    SANDBOX_EXECUTION = "SANDBOX_EXECUTION"
    ARTIFACT_CREATED = "ARTIFACT_CREATED"
    VERIFICATION = "VERIFICATION"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_FAILED = "TASK_FAILED"


class AuditEvent(BaseModel):
    event_id: str
    task_id: str
    event_type: AuditEventType
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_service: str
    actor: str = "agent_orchestrator"
    duration_ms: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class TaskAuditSummary(BaseModel):
    task_id: str
    user: str = "local_operator"
    task_goal: str
    task_classification: Optional[str] = None
    models_selected: List[str] = Field(default_factory=list)
    model_calls_count: int = 0
    total_tokens: int = 0
    tool_calls_count: int = 0
    retrieved_documents: List[str] = Field(default_factory=list)
    source_citations: List[Dict[str, Any]] = Field(default_factory=list)
    sandbox_executions_count: int = 0
    generated_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    completion_status: str = "completed"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    events: List[AuditEvent] = Field(default_factory=list)
