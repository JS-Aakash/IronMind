import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from packages.shared.models.enums import ArtifactType, TaskType
from services.model_gateway.registry import ModelRegistry
from services.model_gateway.router import ModelRouter
from services.model_gateway.router_models import RoutingRequest


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_router_scanned_inspection_approval_note():
    router = ModelRouter()
    req = RoutingRequest(
        goal="Analyze this scanned inspection report for pump P-101, check SOP, and prepare an approval note.",
        attached_files=["inspection_scan_01.pdf"],
    )
    decision = router.route_task(req)

    # Assert task classification and requirements
    assert decision.task_type in [TaskType.DOCUMENT_ANALYSIS, TaskType.APPROVAL_NOTE_GENERATION]
    assert "vision" in decision.required_capabilities
    assert "reasoning" in decision.required_capabilities
    assert decision.requires_rag is True
    assert decision.target_artifact == ArtifactType.DOCX

    # Assert multi-stage model routing
    assert decision.stage_models.get("vision") == "qwen2.5vl:7b"
    assert decision.stage_models.get("reasoning") == "qwen3:8b"
    assert len(decision.candidate_scores) >= 3


def test_router_python_coding_and_sandbox():
    router = ModelRouter()
    req = RoutingRequest(
        goal="Write Python code to calculate pump efficiency with API 610 boundary assertions and run unit tests.",
    )
    decision = router.route_task(req)

    assert decision.task_type == TaskType.CODING
    assert "coding" in decision.required_capabilities
    assert decision.primary_model == "qwen2.5-coder:7b"
    assert decision.requires_sandbox is True
    assert decision.target_artifact == ArtifactType.PYTHON


def test_router_pid_multimodal_analysis():
    router = ModelRouter()
    req = RoutingRequest(
        goal="Inspect this P&ID diagram drawing for Crude Distillation Unit CDU-1 and list all relief valves.",
        attached_files=["cdu1_pid_sheet.png"],
    )
    decision = router.route_task(req)

    assert decision.task_type == TaskType.MULTIMODAL_PID
    assert decision.primary_model == "qwen2.5vl:7b"
    assert "vision" in decision.required_capabilities


def test_router_general_reasoning():
    router = ModelRouter()
    req = RoutingRequest(
        goal="Evaluate refinery energy optimization strategy and draft recommendations for management.",
    )
    decision = router.route_task(req)

    assert decision.task_type == TaskType.GENERAL_REASONING
    assert decision.primary_model == "qwen3:8b"
    assert "reasoning" in decision.required_capabilities


def test_router_user_override():
    router = ModelRouter()
    req = RoutingRequest(
        goal="Calculate pump flow",
        preferred_model="qwen3:8b",
    )
    decision = router.route_task(req)
    assert decision.primary_model == "qwen3:8b"
    assert "override" in decision.routing_reason.lower()


def test_api_router_analyze_endpoint(client):
    payload = {
        "goal": "Analyze scanned inspection report and refer to maintenance SOP",
        "attached_files": ["scan.pdf"],
    }
    response = client.post("/api/v1/router/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["requires_vision"] is True
    assert data["requires_rag"] is True
    assert "task_type" in data


def test_api_router_select_endpoint(client):
    payload = {
        "goal": "Write python script for hydraulic calculation and test in sandbox",
    }
    response = client.post("/api/v1/router/select", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["primary_model"] == "qwen2.5-coder:7b"
    assert data["requires_sandbox"] is True
    assert len(data["candidate_scores"]) >= 3
    assert "explanation" in data
