import asyncio
import logging
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

from packages.shared.models.enums import TaskStatus, TaskType
from packages.shared.utils.helpers import generate_uuid
from services.agent.orchestrator import AgentOrchestrator
from services.agent.state import AgentState, AgentStatus, ExecutionEvent
from services.agent.tools.registry import ToolRegistry
from services.model_gateway.router import ModelRouter
from services.model_gateway.service import ModelService
from services.sovereignty.service import SovereigntyService

import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AgentService:
    """High-level service managing task lifecycles, storage, and agent execution."""

    def __init__(
        self,
        model_service: Optional[ModelService] = None,
        router: Optional[ModelRouter] = None,
        tool_registry: Optional[ToolRegistry] = None,
        sovereignty_service: Optional[SovereigntyService] = None,
        audit_service: Optional[Any] = None,
        storage_dir: str = "storage/tasks",
    ):
        self.model_service = model_service or ModelService()
        self.router = router or ModelRouter()
        self.tool_registry = tool_registry or ToolRegistry()
        self.sovereignty_service = sovereignty_service or SovereigntyService()
        self.audit_service = audit_service or self._init_audit_service()
        self.orchestrator = AgentOrchestrator(
            model_service=self.model_service,
            router=self.router,
            tool_registry=self.tool_registry,
            sovereignty_service=self.sovereignty_service,
            audit_service=self.audit_service,
        )
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, AgentState] = {}
        self._load_tasks()
        if not self._tasks:
            self._initialize_seed_tasks()

    def _init_audit_service(self) -> Any:
        try:
            from services.audit.service import AuditService
            return AuditService()
        except Exception:
            return None

    def _load_tasks(self) -> None:
        """Load persisted task states from storage/tasks/."""
        for task_file in self.storage_dir.glob("*.json"):
            try:
                data = json.loads(task_file.read_text(encoding="utf-8"))
                state = AgentState(**data)
                # Any task left in executing, planning, or pending from previous process runs is not active
                if state.status in [AgentStatus.EXECUTING, AgentStatus.PLANNING, AgentStatus.PENDING]:
                    state.status = AgentStatus.CANCELLED
                    data["status"] = "cancelled"
                    try:
                        task_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    except Exception:
                        pass
                self._tasks[state.task_id] = state
            except Exception as e:
                logger.warning("Could not load persisted task %s: %s", task_file, str(e))

    def _persist_task(self, task_id: str) -> None:
        """Save task state snapshot to disk."""
        state = self._tasks.get(task_id)
        if not state:
            return
        target = self.storage_dir / f"{task_id}.json"
        try:
            target.write_text(json.dumps(state.dict(), default=str, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to persist task state %s: %s", task_id, str(e))

    def _initialize_seed_tasks(self) -> None:
        """Seed realistic industrial tasks for initial dashboard and runs view."""
        sample_task_id = "TASK-MRPL-001"
        self._tasks[sample_task_id] = AgentState(
            task_id=sample_task_id,
            user_goal="Analyze scanned inspection report for Centrifugal Pump P-101 and draft Approval Note DOCX.",
            task_type=TaskType.DOCUMENT_ANALYSIS,
            status=AgentStatus.COMPLETED,
            primary_model="qwen3:8b",
            selected_models={"vision": "qwen2.5vl:7b", "reasoning": "qwen3:8b", "primary": "qwen3:8b"},
            observations=["Vibration velocity 4.8 mm/s exceeds API 610 threshold (4.5 mm/s). Recommended bearing repacking and 30-day vibration monitoring re-audit."],
            generated_artifacts=[{
                "artifact_id": "ART_097ea637",
                "filename": "MRPL_Approval_Note_P101.docx",
                "type": "docx",
                "sha256_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            }],
        )
        self._persist_task(sample_task_id)

        task2_id = "TASK-CALC-002"
        self._tasks[task2_id] = AgentState(
            task_id=task2_id,
            user_goal="Write a Python program to calculate the efficiency of an industrial pump given input power and output power. Validate inputs and run unit tests in sandbox.",
            task_type=TaskType.CODING,
            status=AgentStatus.COMPLETED,
            primary_model="qwen2.5-coder:7b",
            selected_models={"coding": "qwen2.5-coder:7b", "reasoning": "qwen3:8b", "primary": "qwen2.5-coder:7b"},
            observations=["Generated calculate_efficiency module with input validation. Executed 4 boundary unit tests in sandbox: 100% assertions passed, exit code 0."],
            generated_artifacts=[{
                "artifact_id": "ART_e9a1b821",
                "filename": "pump_efficiency.py",
                "type": "python",
                "sha256_hash": "9c82b13c727a85e13d987e918451f28b49e13b8271a4857b29a1b821481e1942",
            }],
        )
        self._persist_task(task2_id)

    def create_task(
        self,
        goal: Any,
        task_type: Optional[TaskType] = None,
        uploaded_files: Optional[List[str]] = None,
    ) -> AgentState:
        """Create a new task state."""
        if hasattr(goal, "goal"):
            actual_goal = goal.goal
            actual_task_type = getattr(goal, "task_type", None) or task_type or TaskType.DOCUMENT_ANALYSIS
            actual_files = getattr(goal, "uploaded_files", None) or uploaded_files or []
        else:
            actual_goal = str(goal)
            actual_task_type = task_type or TaskType.DOCUMENT_ANALYSIS
            actual_files = uploaded_files or []

        task_id = generate_uuid("TASK")
        state = AgentState(
            task_id=task_id,
            user_goal=actual_goal,
            task_type=actual_task_type,
            status=AgentStatus.PENDING,
        )
        self._tasks[task_id] = state
        self._persist_task(task_id)
        self.sovereignty_service.log_event(
            event_type="TASK_CREATED",
            source_service="Agent Service",
            task_id=task_id,
            details={"goal": actual_goal, "task_type": state.task_type.value},
        )
        return state

    def get_task(self, task_id: str) -> Optional[AgentState]:
        """Retrieve task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 50) -> List[AgentState]:
        """List tasks ordered by created_at descending."""
        tasks = list(self._tasks.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    async def execute_task(self, task_id: str, uploaded_files: Optional[List[str]] = None) -> AgentState:
        """Run the full ReAct agent lifecycle on a task."""
        state = self.get_task(task_id)
        if not state:
            raise ValueError(f"Task '{task_id}' not found.")

        # Execute ReAct cycle
        updated_state = await self.orchestrator.run_task(state, uploaded_files=uploaded_files)
        self._tasks[task_id] = updated_state
        self._persist_task(task_id)
        return updated_state

    async def stream_task_events(self, task_id: str) -> AsyncIterator[ExecutionEvent]:
        """Stream execution events for a task via async queue."""
        queue = self.orchestrator.subscribe_events(task_id)
        try:
            while True:
                event = await queue.get()
                yield event
                if event.event_type in ["TASK_COMPLETED", "TASK_FAILED", "TASK_ERROR"]:
                    break
        finally:
            self.orchestrator.unsubscribe_events(task_id, queue)
