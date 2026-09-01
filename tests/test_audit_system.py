from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from services.audit.models import AuditEvent, AuditEventType, TaskAuditSummary
from services.audit.service import AuditService


@pytest.fixture
def audit_service(tmp_path):
    return AuditService(storage_dir=str(tmp_path / "audit"))


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. Event Recording & Aggregation
# ---------------------------------------------------------

def test_audit_event_recording(audit_service):
    task_id = "TASK_PUMP_002"

    # 1. TASK_CREATED
    ev1 = audit_service.record_event(
        task_id=task_id,
        event_type=AuditEventType.TASK_CREATED,
        source_service="Core Gateway",
        details={"goal": "Verify pump P-101 cavitation and calculate NPSHa."},
        actor="refinery_engineer",
    )
    assert ev1.event_type == AuditEventType.TASK_CREATED

    # 2. MODEL_SELECTED
    audit_service.record_event(
        task_id=task_id,
        event_type=AuditEventType.MODEL_SELECTED,
        source_service="Model Router",
        details={"models": ["qwen2.5-coder:7b", "qwen3:8b"]},
    )

    # 3. TOOL_CALLED
    audit_service.record_event(
        task_id=task_id,
        event_type=AuditEventType.TOOL_CALLED,
        source_service="Tool System",
        details={"tool_name": "calculator", "status": "success"},
        duration_ms=4.2,
    )

    # 4. SANDBOX_EXECUTION
    audit_service.record_event(
        task_id=task_id,
        event_type=AuditEventType.SANDBOX_EXECUTION,
        source_service="Sandbox Engine",
        details={"exit_code": 0, "status": "success", "tests_passed": 2},
        duration_ms=850.0,
    )

    # 5. TASK_COMPLETED
    audit_service.record_event(
        task_id=task_id,
        event_type=AuditEventType.TASK_COMPLETED,
        source_service="Agent Orchestrator",
        details={"completion_status": "completed"},
        duration_ms=2500.0,
    )

    # Verify Task Audit Summary
    summary = audit_service.get_task_audit(task_id)
    assert summary is not None
    assert summary.task_id == task_id
    assert summary.completion_status == "completed"
    assert summary.tool_calls_count == 1
    assert summary.sandbox_executions_count == 1
    assert "qwen2.5-coder:7b" in summary.models_selected
    assert len(summary.events) == 5


# ---------------------------------------------------------
# 2. Append-Only Ledger & Task Snapshot Persistence
# ---------------------------------------------------------

def test_audit_ledger_disk_persistence(tmp_path):
    storage_dir = tmp_path / "audit_test"
    svc1 = AuditService(storage_dir=str(storage_dir))
    task_id = "TASK_PERSIST_001"

    svc1.record_event(
        task_id=task_id,
        event_type=AuditEventType.ARTIFACT_CREATED,
        source_service="Artifact Engine",
        details={"artifact_id": "ART_123", "filename": "report.docx", "sha256": "abc12345"},
    )

    ledger_path = storage_dir / "audit_ledger.jsonl"
    assert ledger_path.exists()
    lines = ledger_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    assert "ART_123" in lines[-1]

    # Reload in a new service instance to verify persistence
    svc2 = AuditService(storage_dir=str(storage_dir))
    reloaded = svc2.get_task_audit(task_id)
    assert reloaded is not None
    assert len(reloaded.generated_artifacts) == 1


# ---------------------------------------------------------
# 3. REST API Endpoint Tests for Audit & Provenance
# ---------------------------------------------------------

def test_api_audit_endpoints(client):
    # 1. GET /api/v1/audit
    list_res = client.get("/api/v1/audit")
    assert list_res.status_code == 200
    trails = list_res.json()
    assert isinstance(trails, list)
    assert len(trails) >= 1

    # Sample seeded task ID
    sample_task_id = "TASK_INSPECT_001"

    # 2. GET /api/v1/audit/{task_id}
    get_res = client.get(f"/api/v1/audit/{sample_task_id}")
    assert get_res.status_code == 200
    task_data = get_res.json()
    assert task_data["task_id"] == sample_task_id
    assert task_data["task_classification"] == "document_analysis_and_reasoning"
    assert len(task_data["models_selected"]) >= 2
    assert len(task_data["events"]) >= 8

    # 3. GET /api/v1/audit/{task_id}/events
    events_res = client.get(f"/api/v1/audit/{sample_task_id}/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert isinstance(events, list)
    assert any(e["event_type"] == "TASK_CREATED" for e in events)
    assert any(e["event_type"] == "ARTIFACT_CREATED" for e in events)

    # 4. GET /api/v1/audit/logs
    logs_res = client.get("/api/v1/audit/logs")
    assert logs_res.status_code == 200
    assert isinstance(logs_res.json(), list)
