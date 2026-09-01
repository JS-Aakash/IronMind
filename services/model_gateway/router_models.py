from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from packages.shared.models.enums import ArtifactType, TaskType


class RoutingRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="Task goal, prompt, or engineering description")
    attached_files: List[str] = Field(default_factory=list, description="List of filenames, extensions, or file paths")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional industrial context (e.g. equipment_id)")
    preferred_model: Optional[str] = Field(default=None, description="Optional user-forced model override")


class CapabilityAnalysis(BaseModel):
    task_type: TaskType
    detected_capabilities: List[str]
    requires_vision: bool = False
    requires_coding: bool = False
    requires_reasoning: bool = True
    requires_rag: bool = False
    requires_sandbox: bool = False
    requires_artifact_generation: bool = False
    target_artifact_type: Optional[ArtifactType] = None
    matched_keywords: Dict[str, List[str]] = Field(default_factory=dict)


class ModelScore(BaseModel):
    model_name: str
    display_name: str
    total_score: float
    capability_score: float
    task_fit_score: float
    hardware_fit_score: float
    matched_capabilities: List[str]
    is_available: bool = True
    explanation: str


class StageRouting(BaseModel):
    stage_name: str
    required_capability: str
    selected_model: str
    reason: str


class RoutingDecision(BaseModel):
    task_type: TaskType
    primary_model: str
    stage_models: Dict[str, str] = Field(default_factory=dict, description="Per-stage model allocation (e.g. vision -> qwen2.5vl:7b, reasoning -> qwen3:8b)")
    stages: List[StageRouting] = Field(default_factory=list)
    required_capabilities: List[str]
    candidate_scores: List[ModelScore]
    alternatives: List[str] = Field(default_factory=list)
    requires_sandbox: bool = False
    requires_rag: bool = False
    target_artifact: Optional[ArtifactType] = None
    routing_reason: str
    explanation: str
