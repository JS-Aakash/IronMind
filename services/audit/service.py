import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from packages.shared.utils.helpers import generate_uuid
from services.audit.models import AuditEvent, AuditEventType, TaskAuditSummary
from services.sovereignty.service import SovereigntyService

logger = logging.getLogger(__name__)


class AuditService:
    """Enterprise Sovereign Audit and Provenance Service."""

    def __init__(
        self,
        storage_dir: str = "storage/audit",
        sovereignty_service: Optional[SovereigntyService] = None,
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_dir = self.storage_dir / "tasks"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.storage_dir / "audit_ledger.jsonl"
        self.sovereignty_service = sovereignty_service or SovereigntyService()

        self._task_trails: Dict[str, TaskAuditSummary] = {}
        self._load_task_trails()
        if not self._task_trails:
            self._seed_sample_audit_trail()

    def _load_task_trails(self) -> None:
        """Load task audit trail snapshots from storage/audit/tasks/."""
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                data = json.loads(task_file.read_text(encoding="utf-8"))
                trail = TaskAuditSummary(**data)
                self._task_trails[trail.task_id] = trail
            except Exception as e:
                logger.warning("Could not load audit task file %s: %s", task_file, str(e))

    def _persist_task(self, task_id: str) -> None:
        """Persist updated task audit summary to disk."""
        trail = self._task_trails.get(task_id)
        if not trail:
            return
        target = self.tasks_dir / f"{task_id}.json"
        try:
            target.write_text(json.dumps(trail.dict(), indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to persist task audit snapshot for %s: %s", task_id, str(e))

    def _append_to_ledger(self, event: AuditEvent) -> None:
        """Append event to immutable JSONL audit ledger."""
        try:
            with self.ledger_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event.dict()) + "\n")
        except Exception as e:
            logger.error("Failed to append to audit ledger: %s", str(e))

    def _seed_sample_audit_trail(self) -> None:
        """Seed complete high-fidelity audit trail for MRPL Slurry Pump P-101 approval note generation."""
        task_id = "TASK_INSPECT_001"
        created_at = "2026-09-01T06:00:00.000000"
        completed_at = "2026-09-01T06:00:12.450000"

        events_data = [
            (
                AuditEventType.TASK_CREATED,
                "Core Gateway",
                "local_operator",
                0.0,
                {"goal": "Analyze scanned inspection report for pump P-101 and generate formal approval note."},
            ),
            (
                AuditEventType.TASK_CLASSIFIED,
                "Model Router",
                "qwen3:0.6b",
                45.2,
                {"task_type": "document_analysis_and_reasoning", "required_capabilities": ["vision", "reasoning", "rag", "artifact_generation"]},
            ),
            (
                AuditEventType.MODEL_SELECTED,
                "Model Router",
                "router_engine",
                12.0,
                {"stages": {"vision": "qwen2.5vl:7b", "reasoning": "qwen3:8b"}, "reason": "Dual-stage pipeline routed vision to Qwen2.5-VL and SOP reasoning to Qwen3."},
            ),
            (
                AuditEventType.TOOL_CALLED,
                "Tool System",
                "agent_orchestrator",
                150.0,
                {"tool_name": "document.ocr_parse", "arguments_digest": "sha256_e819b4... (scanned_p101_report.png)", "status": "success"},
            ),
            (
                AuditEventType.MODEL_INFERENCE,
                "Model Gateway",
                "qwen2.5vl:7b",
                2100.5,
                {"model": "qwen2.5vl:7b", "prompt_tokens": 580, "completion_tokens": 128, "extracted_tags": ["P-101", "ISO-10816"], "measured_vibration": 4.8},
            ),
            (
                AuditEventType.RAG_RETRIEVAL,
                "RAG Engine",
                "agent_orchestrator",
                32.8,
                {"query": "P-101 vibration threshold ISO 10816", "top_k": 2, "matched_docs": ["MRPL_SOP_P101_Pump_Maintenance.pdf (Page 2)"], "citation_count": 2},
            ),
            (
                AuditEventType.MODEL_INFERENCE,
                "Model Gateway",
                "qwen3:8b",
                4800.0,
                {"model": "qwen3:8b", "prompt_tokens": 850, "completion_tokens": 420, "action": "synthesize_approval_note", "reasoning_steps": 4},
            ),
            (
                AuditEventType.ARTIFACT_CREATED,
                "Artifact Engine",
                "docx_generator",
                340.2,
                {"artifact_id": "ART_097ea637", "filename": "MRPL_Approval_Note_P_101.docx", "format": "docx", "sha256": "8e28c4ab69992fa150c1134bc4d7e3422d3d44635bccc9f782fc2f47cd9be0ae", "size_bytes": 38227},
            ),
            (
                AuditEventType.VERIFICATION,
                "Agent Verifier",
                "agent_verifier",
                85.0,
                {"verification_passed": True, "checks": ["artifact_non_empty", "sop_citations_present", "signature_blocks_verified"]},
            ),
            (
                AuditEventType.TASK_COMPLETED,
                "Agent Orchestrator",
                "agent_orchestrator",
                12450.0,
                {"completion_status": "completed", "artifacts_count": 1, "egress_bytes": 0},
            ),
        ]

        events: List[AuditEvent] = []
        for ev_type, src, actor, dur, details in events_data:
            ev = AuditEvent(
                event_id=generate_uuid("EVT"),
                task_id=task_id,
                event_type=ev_type,
                timestamp=created_at,
                source_service=src,
                actor=actor,
                duration_ms=dur,
                details=details,
            )
            events.append(ev)
            self._append_to_ledger(ev)

        summary = TaskAuditSummary(
            task_id=task_id,
            user="aakash_engineer",
            task_goal="Analyze scanned inspection report for pump P-101 and generate formal approval note.",
            task_classification="document_analysis_and_reasoning",
            models_selected=["qwen2.5vl:7b", "qwen3:8b"],
            model_calls_count=2,
            total_tokens=1978,
            tool_calls_count=2,
            retrieved_documents=["MRPL_SOP_P101_Pump_Maintenance.pdf"],
            source_citations=[{"document": "MRPL_SOP_P101_Pump_Maintenance.pdf", "page": 2, "section": "Section 4.2"}],
            sandbox_executions_count=0,
            generated_artifacts=[{"artifact_id": "ART_097ea637", "filename": "MRPL_Approval_Note_P_101.docx", "type": "docx"}],
            errors=[],
            completion_status="completed",
            created_at=created_at,
            completed_at=completed_at,
            duration_ms=12450.0,
            events=events,
        )
        self._task_trails[task_id] = summary
        self._persist_task(task_id)

    def record_event(
        self,
        task_id: str,
        event_type: AuditEventType,
        source_service: str,
        details: Dict[str, Any],
        duration_ms: Optional[float] = None,
        actor: str = "agent_orchestrator",
    ) -> AuditEvent:
        """Record and append an audit event to the chronological task timeline and ledger."""
        event = AuditEvent(
            event_id=generate_uuid("EVT"),
            task_id=task_id,
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            source_service=source_service,
            actor=actor,
            duration_ms=duration_ms,
            details=details,
        )

        if task_id not in self._task_trails:
            self._task_trails[task_id] = TaskAuditSummary(
                task_id=task_id,
                task_goal=details.get("goal", "Autonomous task execution"),
                created_at=datetime.utcnow().isoformat(),
            )

        trail = self._task_trails[task_id]
        trail.events.append(event)

        # Update aggregated stats
        if event_type == AuditEventType.MODEL_SELECTED:
            models = details.get("models") or list(details.get("stages", {}).values())
            trail.models_selected.extend([m for m in models if m not in trail.models_selected])
        elif event_type == AuditEventType.MODEL_INFERENCE:
            trail.model_calls_count += 1
            trail.total_tokens += details.get("prompt_tokens", 0) + details.get("completion_tokens", 0)
        elif event_type == AuditEventType.TOOL_CALLED:
            trail.tool_calls_count += 1
        elif event_type == AuditEventType.RAG_RETRIEVAL:
            docs = details.get("matched_docs", [])
            trail.retrieved_documents.extend([d for d in docs if d not in trail.retrieved_documents])
        elif event_type == AuditEventType.SANDBOX_EXECUTION:
            trail.sandbox_executions_count += 1
        elif event_type == AuditEventType.ARTIFACT_CREATED:
            trail.generated_artifacts.append(details)
        elif event_type == AuditEventType.TASK_COMPLETED:
            trail.completion_status = "completed"
            trail.completed_at = datetime.utcnow().isoformat()
            if duration_ms:
                trail.duration_ms = duration_ms
        elif event_type == AuditEventType.TASK_FAILED:
            trail.completion_status = "failed"
            trail.completed_at = datetime.utcnow().isoformat()
            trail.errors.append(details.get("error", "Unknown task failure"))

        self._append_to_ledger(event)
        self._persist_task(task_id)
        return event

    def get_task_audit(self, task_id: str) -> Optional[TaskAuditSummary]:
        return self._task_trails.get(task_id)

    def list_audit_trails(self, limit: int = 50) -> List[TaskAuditSummary]:
        trails = list(self._task_trails.values())
        trails.sort(key=lambda t: t.created_at, reverse=True)
        return trails[:limit]

    def list_task_events(self, task_id: str) -> List[AuditEvent]:
        trail = self._task_trails.get(task_id)
        return trail.events if trail else []
