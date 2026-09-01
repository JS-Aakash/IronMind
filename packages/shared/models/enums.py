from enum import Enum


class TaskType(str, Enum):
    DOCUMENT_ANALYSIS = "document_analysis"
    CODING = "coding"
    MULTIMODAL_PID = "multimodal_pid"
    ENGINEERING_CALC = "engineering_calc"
    GENERAL_REASONING = "general_reasoning"
    APPROVAL_NOTE_GENERATION = "approval_note_generation"


class TaskStatus(str, Enum):
    PENDING = "pending"
    CLASSIFYING = "classifying"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelRole(str, Enum):
    REASONING = "reasoning"
    VISION = "vision"
    CODING = "coding"
    EMBEDDING = "embedding"
    ROUTING = "routing"


class ModelStatus(str, Enum):
    LOADED = "loaded"
    STANDBY = "standby"
    UNLOADED = "unloaded"
    ERROR = "error"


class ArtifactType(str, Enum):
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    PDF = "pdf"
    PYTHON = "python"
    JSON = "json"


class SovereigntyStatus(str, Enum):
    AIRGAPPED = "airgapped"
    VERIFIED_LOCAL = "verified_local"
    WARNING = "warning"
    BREACH = "breach"
