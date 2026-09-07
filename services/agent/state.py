from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, computed_field, model_validator

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
    called_at: datetime = Field(default_factory=datetime.now)


class VerificationResult(BaseModel):
    passed: bool
    checks_performed: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    recommendation: Optional[str] = None
    verified_at: datetime = Field(default_factory=datetime.now)


class ExecutionEvent(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    stage: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class RecoveryAttempt(BaseModel):
    attempt_number: int  # 1, 2, 3, 4
    tool_name: str
    code_or_input: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    test_results: Optional[str] = None
    failure_details: Optional[str] = None
    is_recoverable: bool = True
    root_cause_analysis: Optional[str] = None
    fix_description: Optional[str] = None
    status: str = "running"  # "running", "failed", "analyzing", "fixing", "verified", "halted"
    timestamp: datetime = Field(default_factory=datetime.now)



class AgentState(BaseModel):
    task_id: str
    user_goal: str
    task_type: TaskType
    status: AgentStatus = AgentStatus.PENDING

    @computed_field
    @property
    def goal(self) -> str:
        """Alias for user_goal to maintain frontend and API compatibility."""
        return self.user_goal

    @model_validator(mode="before")
    @classmethod
    def handle_goal_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "user_goal" not in data and "goal" in data:
                data["user_goal"] = data["goal"]
        return data
    plan: List[PlanStep] = Field(default_factory=list)
    current_step_index: int = 0
    primary_model: Optional[str] = None
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
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    execution_trace: List[Dict[str, Any]] = Field(default_factory=list)
    current_streaming_text: Optional[str] = None
    streaming_model: Optional[str] = None
    change_summaries: List[Dict[str, Any]] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    recovery_attempts: List[RecoveryAttempt] = Field(default_factory=list)
    user_intervention_prompt: Optional[str] = None


