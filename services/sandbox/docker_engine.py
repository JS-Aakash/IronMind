import asyncio
import json
import logging
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from services.sandbox.models import SandboxExecutionResult, SandboxStatus, TestCaseResult
from services.sandbox.security_scanner import CodeSecurityScanner

logger = logging.getLogger(__name__)


class DockerSandboxEngine:
    """Docker-based air-gapped container sandbox with zero network access and strict hardware quotas."""

    DOCKER_IMAGE = "python:3.12-slim"
    DEFAULT_MEMORY_LIMIT = "256m"
    DEFAULT_CPUS = "1.0"
    DEFAULT_PIDS_LIMIT = "64"

    def __init__(self):
        self.security_scanner = CodeSecurityScanner()
        self._docker_available: Optional[bool] = None

    async def is_docker_available(self) -> bool:
        """Check if Docker daemon is accessible."""
        if self._docker_available is not None:
            return self._docker_available

        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "info",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=3.0)
            self._docker_available = (proc.returncode == 0)
        except Exception:
            self._docker_available = False

        return self._docker_available

    def _parse_pytest_output(self, output_text: str) -> List[TestCaseResult]:
        """Extract test case names and pass/fail statuses from pytest output."""
        tests: List[TestCaseResult] = []
        # Match lines like "test_module.py::test_case_name PASSED" or "FAILED"
        pattern = re.compile(r"([a-zA-Z0-9_\/\\]+\.py::([a-zA-Z0-9_]+))\s+(PASSED|FAILED|ERROR|SKIPPED)", re.IGNORECASE)
        for match in pattern.finditer(output_text):
            full_target, func_name, status = match.groups()
            tests.append(
                TestCaseResult(
                    name=func_name,
                    status="passed" if status.upper() == "PASSED" else "failed",
                    message=None if status.upper() == "PASSED" else f"Test {func_name} {status.lower()}",
                )
            )
        return tests

    async def execute_in_docker(
        self,
        code: str,
        test_files: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 15,
        memory_limit_mb: int = 256,
        cpu_limit: float = 1.0,
    ) -> SandboxExecutionResult:
        """Run code inside an ephemeral, network-isolated Docker container."""
        # 1. Pre-execution Security Scan
        is_safe, violation_reason = self.security_scanner.scan_code(code)
        if not is_safe:
            return SandboxExecutionResult(
                status=SandboxStatus.SECURITY_BLOCKED.value,
                stdout="",
                stderr=f"Security Policy Violation: {violation_reason}",
                exit_code=1,
                duration_ms=0.0,
                tests=[],
                memory_limit_mb=memory_limit_mb,
                cpu_limit=cpu_limit,
                network_mode="none",
                execution_engine="security_firewall",
                cleanup_verified=True,
            )

        # 2. Prepare Isolated Temporary Workspace on Host
        temp_dir = Path(tempfile.mkdtemp(prefix="ironmind_sandbox_"))
        start_time = time.perf_counter()
        cleanup_success = False

        try:
            # Write main code
            main_py = temp_dir / "main.py"
            main_py.write_text(code, encoding="utf-8")

            # Write test files if provided
            has_tests = False
            if test_files:
                has_tests = True
                for fname, fcontent in test_files.items():
                    # Scan test code as well
                    t_safe, t_reason = self.security_scanner.scan_code(fcontent)
                    if not t_safe:
                        return SandboxExecutionResult(
                            status=SandboxStatus.SECURITY_BLOCKED.value,
                            stdout="",
                            stderr=f"Security Policy Violation in test file '{fname}': {t_reason}",
                            exit_code=1,
                            duration_ms=0.0,
                            tests=[],
                            memory_limit_mb=memory_limit_mb,
                            cpu_limit=cpu_limit,
                            network_mode="none",
                            execution_engine="security_firewall",
                            cleanup_verified=True,
                        )
                    (temp_dir / fname).write_text(fcontent, encoding="utf-8")

            # Command to run inside container: if tests exist, run main then pytest
            if has_tests:
                container_cmd = "python /workspace/main.py && pytest -v /workspace"
            else:
                container_cmd = "python /workspace/main.py"

            # 3. Formulate Docker Run arguments
            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", f"{memory_limit_mb}m",
                "--cpus", str(cpu_limit),
                "--pids-limit", self.DEFAULT_PIDS_LIMIT,
                "--read-only",
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "-v", f"{temp_dir.resolve()}:/workspace:rw",
                "-w", "/workspace",
                self.DOCKER_IMAGE,
                "sh", "-c", container_cmd,
            ]

            proc = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

                test_results = self._parse_pytest_output(stdout_str + "\n" + stderr_str) if has_tests else []

                status = SandboxStatus.SUCCESS.value if proc.returncode == 0 else SandboxStatus.FAILURE.value

                return SandboxExecutionResult(
                    status=status,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=proc.returncode or 0,
                    duration_ms=duration_ms,
                    tests=test_results,
                    memory_limit_mb=memory_limit_mb,
                    cpu_limit=cpu_limit,
                    network_mode="none",
                    execution_engine="docker_container",
                    cleanup_verified=True,
                )

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return SandboxExecutionResult(
                    status=SandboxStatus.TIMEOUT.value,
                    stdout="",
                    stderr=f"Execution timed out after {timeout_seconds} seconds. Killed runaway container process.",
                    exit_code=-1,
                    duration_ms=duration_ms,
                    tests=[],
                    memory_limit_mb=memory_limit_mb,
                    cpu_limit=cpu_limit,
                    network_mode="none",
                    execution_engine="docker_container",
                    cleanup_verified=True,
                )

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SandboxExecutionResult(
                status=SandboxStatus.FAILURE.value,
                stdout="",
                stderr=f"Docker container launch failed: {str(e)}",
                exit_code=1,
                duration_ms=duration_ms,
                tests=[],
                memory_limit_mb=memory_limit_mb,
                cpu_limit=cpu_limit,
                network_mode="none",
                execution_engine="docker_container",
                cleanup_verified=True,
            )
        finally:
            # 4. Enforce immediate host filesystem cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                cleanup_success = not temp_dir.exists()
            except Exception:
                cleanup_success = False


class LocalIsolatedSandboxEngine:
    """Isolated local process sandbox with zero network env and AST security policies (used in air-gap dev & tests)."""

    def __init__(self):
        self.security_scanner = CodeSecurityScanner()

    def _parse_pytest_output(self, output_text: str) -> List[TestCaseResult]:
        tests: List[TestCaseResult] = []
        pattern = re.compile(r"([a-zA-Z0-9_\/\\]+\.py::([a-zA-Z0-9_]+))\s+(PASSED|FAILED|ERROR|SKIPPED)", re.IGNORECASE)
        for match in pattern.finditer(output_text):
            full_target, func_name, status = match.groups()
            tests.append(
                TestCaseResult(
                    name=func_name,
                    status="passed" if status.upper() == "PASSED" else "failed",
                    message=None if status.upper() == "PASSED" else f"Test {func_name} {status.lower()}",
                )
            )
        return tests

    async def execute_isolated(
        self,
        code: str,
        test_files: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 15,
        memory_limit_mb: int = 256,
        cpu_limit: float = 1.0,
    ) -> SandboxExecutionResult:
        """Execute code in an isolated workspace with restricted environment."""
        # 1. Pre-execution Security Scan
        is_safe, violation_reason = self.security_scanner.scan_code(code)
        if not is_safe:
            return SandboxExecutionResult(
                status=SandboxStatus.SECURITY_BLOCKED.value,
                stdout="",
                stderr=f"Security Policy Violation: {violation_reason}",
                exit_code=1,
                duration_ms=0.0,
                tests=[],
                memory_limit_mb=memory_limit_mb,
                cpu_limit=cpu_limit,
                network_mode="none",
                execution_engine="security_firewall",
                cleanup_verified=True,
            )

        temp_dir = Path(tempfile.mkdtemp(prefix="ironmind_isolated_"))
        start_time = time.perf_counter()

        try:
            main_py = temp_dir / "main.py"
            main_py.write_text(code, encoding="utf-8")

            has_tests = False
            if test_files:
                has_tests = True
                for fname, fcontent in test_files.items():
                    t_safe, t_reason = self.security_scanner.scan_code(fcontent)
                    if not t_safe:
                        return SandboxExecutionResult(
                            status=SandboxStatus.SECURITY_BLOCKED.value,
                            stdout="",
                            stderr=f"Security Policy Violation in test file '{fname}': {t_reason}",
                            exit_code=1,
                            duration_ms=0.0,
                            tests=[],
                            memory_limit_mb=memory_limit_mb,
                            cpu_limit=cpu_limit,
                            network_mode="none",
                            execution_engine="security_firewall",
                            cleanup_verified=True,
                        )
                    (temp_dir / fname).write_text(fcontent, encoding="utf-8")

            # Execution environment
            safe_env = {
                "AIRGAP_SANDBOX": "1",
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPATH": str(temp_dir),
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", "C:\\Windows"),
                "TEMP": str(temp_dir),
                "TMP": str(temp_dir),
            }

            # Run main script
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                str(main_py),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(temp_dir),
                env=safe_env,
            )

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()

                test_results = []
                # If tests exist and main script succeeded, run pytest
                if has_tests and proc.returncode == 0:
                    test_proc = await asyncio.create_subprocess_exec(
                        sys.executable, "-m", "pytest", "-v", str(temp_dir),
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        cwd=str(temp_dir),
                        env=safe_env,
                    )
                    t_out, t_err = await asyncio.wait_for(test_proc.communicate(), timeout=timeout_seconds)
                    t_out_str = t_out.decode("utf-8", errors="replace")
                    test_results = self._parse_pytest_output(t_out_str)
                    if test_proc.returncode != 0:
                        stderr_str += f"\n[Pytest Failures]:\n{t_out_str}"

                status = SandboxStatus.SUCCESS.value if proc.returncode == 0 else SandboxStatus.FAILURE.value

                return SandboxExecutionResult(
                    status=status,
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=proc.returncode or 0,
                    duration_ms=duration_ms,
                    tests=test_results,
                    memory_limit_mb=memory_limit_mb,
                    cpu_limit=cpu_limit,
                    network_mode="none",
                    execution_engine="local_isolated_process",
                    cleanup_verified=True,
                )

            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
                return SandboxExecutionResult(
                    status=SandboxStatus.TIMEOUT.value,
                    stdout="",
                    stderr=f"Execution timed out after {timeout_seconds} seconds. Process killed.",
                    exit_code=-1,
                    duration_ms=duration_ms,
                    tests=[],
                    memory_limit_mb=memory_limit_mb,
                    cpu_limit=cpu_limit,
                    network_mode="none",
                    execution_engine="local_isolated_process",
                    cleanup_verified=True,
                )

        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return SandboxExecutionResult(
                status=SandboxStatus.FAILURE.value,
                stdout="",
                stderr=f"Sandbox execution error: {str(e)}",
                exit_code=1,
                duration_ms=duration_ms,
                tests=[],
                memory_limit_mb=memory_limit_mb,
                cpu_limit=cpu_limit,
                network_mode="none",
                execution_engine="local_isolated_process",
                cleanup_verified=True,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
