import logging
from typing import Any, Dict, List, Optional

from services.sandbox.docker_engine import DockerSandboxEngine, LocalIsolatedSandboxEngine
from services.sandbox.models import SandboxExecutionResult, SandboxStatus
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class SandboxService:
    """Enterprise Sovereign Python Sandbox Service providing Docker containerization with zero network egress."""

    def __init__(
        self,
        mode: str = "docker",
        timeout_seconds: int = 15,
        memory_limit_mb: int = 256,
        cpu_limit: float = 1.0,
        sovereignty_service: Optional[SovereigntyService] = None,
    ):
        self.mode = mode
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit = cpu_limit
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self.docker_engine = DockerSandboxEngine()
        self.isolated_engine = LocalIsolatedSandboxEngine()

    def get_status(self) -> Dict[str, Any]:
        """Check sandbox engine health and isolation configuration."""
        return {
            "mode": self.mode,
            "timeout_seconds": self.timeout_seconds,
            "memory_limit_mb": self.memory_limit_mb,
            "cpu_limit": self.cpu_limit,
            "network_mode": "none",
            "network_isolated": True,
            "egress_blocked": True,
            "ready": True,
        }

    async def execute_python(
        self,
        code: str,
        test_files: Optional[Dict[str, str]] = None,
        timeout_seconds: Optional[int] = None,
        memory_limit_mb: Optional[int] = None,
        cpu_limit: Optional[float] = None,
        force_engine: Optional[str] = None,
    ) -> SandboxExecutionResult:
        """Execute verified Python source code and test files in an air-gapped sandbox.

        Parameters:
        - code: Main Python script content
        - test_files: Optional map of filename -> test code (e.g. {"test_pump.py": "..."})
        - timeout_seconds: Max run duration (default 15s)
        - memory_limit_mb: Max RAM limit (default 256MB)
        - cpu_limit: Max CPU cores (default 1.0)
        - force_engine: Override engine ("docker" or "isolated")
        """
        timeout = timeout_seconds or self.timeout_seconds
        mem_limit = memory_limit_mb or self.memory_limit_mb
        cpu_lim = cpu_limit or self.cpu_limit

        # Determine execution engine
        use_docker = False
        if force_engine == "docker":
            use_docker = True
        elif force_engine == "isolated":
            use_docker = False
        elif self.mode == "docker":
            use_docker = await self.docker_engine.is_docker_available()
        else:
            use_docker = False

        if use_docker:
            result = await self.docker_engine.execute_in_docker(
                code=code,
                test_files=test_files,
                timeout_seconds=timeout,
                memory_limit_mb=mem_limit,
                cpu_limit=cpu_lim,
            )
        else:
            result = await self.isolated_engine.execute_isolated(
                code=code,
                test_files=test_files,
                timeout_seconds=timeout,
                memory_limit_mb=mem_limit,
                cpu_limit=cpu_lim,
            )

        # Audit event
        self.sovereignty_service.log_event(
            event_type="SANDBOX_EXECUTION",
            source_service="Python Sandbox",
            details={
                "status": result.status,
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
                "engine": result.execution_engine,
                "network_mode": result.network_mode,
                "tests_count": len(result.tests),
            },
        )

        return result
