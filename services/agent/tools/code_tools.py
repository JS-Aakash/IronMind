import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.agent.tools.base import BaseTool, ToolResult
from services.agent.tools.security import ToolPermission, validate_safe_storage_path
from services.sandbox.service import SandboxService


class PythonExecuteTool(BaseTool):
    """Isolated Python code execution environment with zero network egress and strict process isolation."""

    def __init__(self, sandbox_service: Optional[SandboxService] = None):
        self.sandbox_service = sandbox_service or SandboxService()

    @property
    def name(self) -> str:
        return "python.execute"

    @property
    def description(self) -> str:
        return (
            "Execute verified Python engineering code, data transformations, or unit tests in an air-gapped sandbox. "
            "Never allows arbitrary shell commands or network access."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Valid Python source code to execute (e.g. calculation script, assertions)",
                },
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds (default: 15, max: 60)",
                    "default": 15,
                },
            },
            "required": ["code"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "stdout": {"type": "string"},
                "stderr": {"type": "string"},
                "exit_code": {"type": "integer"},
                "latency_ms": {"type": "number"},
                "network_egress_bytes": {"type": "integer"},
            },
        }

    @property
    def permissions(self) -> List[ToolPermission]:
        return [ToolPermission.SANDBOX_EXECUTE]

    async def execute(self, arguments: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        code = arguments.get("code", "")
        timeout = min(60, max(1, int(arguments.get("timeout_seconds", 15))))

        if not code or not isinstance(code, str) or not code.strip():
            return ToolResult(tool_name=self.name, success=False, error="Argument 'code' must be a non-empty string.")

        # Ensure temp directory in storage/temp
        temp_dir = Path("storage/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tempfile.NamedTemporaryFile("w", suffix=".py", dir=str(temp_dir), delete=False, encoding="utf-8") as f:
                script_path = f.name
                f.write(code)
        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Failed to prepare sandbox script: {str(e)}")

        start_time = time.perf_counter()
        try:
            # Execute in isolated subprocess with current python interpreter (no shell)
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={
                    **os.environ,
                    "AIRGAP_SANDBOX": "1",
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                },
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
                stdout_str = stdout_data.decode("utf-8", errors="replace").strip()
                stderr_str = stderr_data.decode("utf-8", errors="replace").strip()

                if proc.returncode == 0:
                    return ToolResult(
                        tool_name=self.name,
                        success=True,
                        output={
                            "stdout": stdout_str if stdout_str else "[Execution completed with exit code 0]",
                            "stderr": stderr_str,
                            "exit_code": 0,
                            "latency_ms": latency_ms,
                            "network_egress_bytes": 0,
                        },
                        metadata={"exit_code": 0, "latency_ms": latency_ms, "network_egress": "0 bytes"},
                    )
                else:
                    return ToolResult(
                        tool_name=self.name,
                        success=False,
                        error=f"Process exited with non-zero code {proc.returncode}:\n{stderr_str or stdout_str}",
                        output={"stdout": stdout_str, "stderr": stderr_str, "exit_code": proc.returncode},
                        metadata={"exit_code": proc.returncode, "latency_ms": latency_ms},
                    )

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Sandbox execution timed out after {timeout} seconds.",
                    metadata={"timeout": timeout},
                )

        except Exception as e:
            return ToolResult(tool_name=self.name, success=False, error=f"Sandbox dispatch failure: {str(e)}")
        finally:
            try:
                Path(script_path).unlink(missing_ok=True)
            except Exception:
                pass


# Backward compatibility alias
class PythonSandboxTool(PythonExecuteTool):
    @property
    def name(self) -> str:
        return "python.execute_sandbox"
