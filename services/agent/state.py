from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from packages.shared.models.enums import ArtifactType, TaskStatus, TaskType


class AgentStatus(str, Enum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    ITERATING = "iterating"
    HUMAN_REVIEW_REQUIRED = "human_review_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PlanStep(BaseModel):
    step_id: str
    order: int
    title: str
    description: str
    tool_name: Optional[str] = None
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    assigned_model: Optional[str] = None
    status: AgentStatus = AgentStatus.PENDING
    observation: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class ToolCallRecord(BaseModel):
    call_id: str
    tool_name: str
    arguments: Dict[str, Any]
    output: Optional[Any] = None
    error: Optional[str] = None
    success: bool
    latency_ms: float = 0.0
    called_at: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    passed: bool
    checks_performed: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionEvent(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    stage: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentState(BaseModel):
    task_id: str
    user_goal: str
    task_type: TaskType
    status: AgentStatus = AgentStatus.PENDING
    plan: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    selected_models: Dict[str, str] = Field(default_factory=dict)
    tool_calls: List[ToolCallRecord] = Field(default_factory=list)
    retrieved_context: List[Dict[str, Any]] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)
    verification_results: Optional[VerificationResult] = None
    generated_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    requires_human_approval: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
