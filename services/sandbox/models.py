from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SandboxStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    SECURITY_BLOCKED = "security_blocked"


class TestCaseResult(BaseModel):
    name: str
    status: str  # "passed" | "failed" | "error"
    duration_ms: Optional[float] = None
    message: Optional[str] = None


class SandboxExecutionResult(BaseModel):
    status: str = Field(description="success | failure | timeout | security_blocked")
    stdout: str = Field(default="")
    stderr: str = Field(default="")
    exit_code: int = Field(default=0)
    duration_ms: float = Field(default=0.0)
    tests: List[TestCaseResult] = Field(default_factory=list)
    memory_limit_mb: int = Field(default=256)
    cpu_limit: float = Field(default=1.0)
    network_mode: str = Field(default="none")
    execution_engine: str = Field(default="docker")
    cleanup_verified: bool = Field(default=True)
