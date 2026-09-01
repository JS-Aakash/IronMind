from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from services.sandbox.models import SandboxExecutionResult
from services.sandbox.service import SandboxService

router = APIRouter()


class SandboxExecuteRequest(BaseModel):
    code: str = Field(description="Python source code to execute")
    test_files: Optional[Dict[str, str]] = Field(default=None, description="Optional map of test filename -> code")
    timeout_seconds: Optional[int] = Field(default=15, ge=1, le=60)
    memory_limit_mb: Optional[int] = Field(default=256, ge=64, le=1024)
    cpu_limit: Optional[float] = Field(default=1.0, ge=0.1, le=4.0)


def get_sandbox_service() -> SandboxService:
    return SandboxService()


@router.get("/status")
def get_sandbox_status(service: SandboxService = Depends(get_sandbox_service)) -> Dict[str, Any]:
    """Retrieve sandbox configuration, hardware quotas, and air-gap isolation status."""
    return service.get_status()


@router.post("/execute", response_model=SandboxExecutionResult)
async def execute_code_endpoint(
    req: SandboxExecuteRequest,
    service: SandboxService = Depends(get_sandbox_service),
) -> SandboxExecutionResult:
    """Safely execute generated Python code in an air-gapped containerized sandbox."""
    return await service.execute_python(
        code=req.code,
        test_files=req.test_files,
        timeout_seconds=req.timeout_seconds,
        memory_limit_mb=req.memory_limit_mb,
        cpu_limit=req.cpu_limit,
    )
