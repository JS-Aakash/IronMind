import pytest
from fastapi.testclient import TestClient

from apps.backend.app.core.dependencies import get_agent_service
from apps.backend.app.main import app
from packages.shared.models.enums import TaskType
from services.agent.orchestrator import AgentOrchestrator
from services.agent.planner import AgentPlanner
from services.agent.service import AgentService
from services.agent.state import AgentState, AgentStatus
from services.agent.tools.registry import ToolRegistry
from services.agent.verifier import AgentVerifier
from services.model_gateway.providers.mock import MockProvider
from services.model_gateway.registry import ModelRegistry
from services.model_gateway.router import ModelRouter
from services.model_gateway.router_models import RoutingRequest
from services.model_gateway.service import ModelService


@pytest.fixture
def mock_agent_service():
    mock_provider = MockProvider()
    registry = ModelRegistry()
    model_svc = ModelService(registry=registry)
    model_svc.register_provider(mock_provider)
    for m in registry.list_models(enabled_only=False):
        m.provider = "mock"
    return AgentService(model_service=model_svc)


@pytest.fixture
def client(mock_agent_service):
    app.dependency_overrides[get_agent_service] = lambda: mock_agent_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_tool_registry_invocations():
    registry = ToolRegistry()
    assert len(registry.list_tools()) >= 5

    # 1. Test Knowledge Search Tool
    k_res, k_rec = await registry.invoke_tool("knowledge.search", {"query": "vibration threshold pump P-101"})
    assert k_res.success is True
    assert k_rec.success is True
    assert len(k_res.output) > 0

    # 2. Test Document OCR Parse Tool
    d_res, d_rec = await registry.invoke_tool("document.ocr_parse", {"file_path": "scan.pdf"})
    assert d_res.success is True
    assert "equipment_id" in d_res.output

    # 3. Test Artifact Generate DOCX Tool
    a_res, a_rec = await registry.invoke_tool(
        "artifact.generate_docx",
        {
            "subject": "Pump Inspection Review",
            "equipment_id": "P-101",
            "findings": ["Bearing vibration 4.8 mm/s"],
            "recommended_action": "Replace bearing",
        },
    )
    assert a_res.success is True
    assert "sha256_hash" in a_res.output
    assert a_res.output["verified"] is True

    # 4. Test Python Sandbox Tool
    code_snippet = "x = 10\ny = 20\nassert x + y == 30\nprint('SUCCESS')"
    p_res, p_rec = await registry.invoke_tool("python.execute_sandbox", {"code": code_snippet})
    assert p_res.success is True
    assert "SUCCESS" in str(p_res.output)


@pytest.mark.asyncio
async def test_agent_planner_generation():
    planner = AgentPlanner()
    router = ModelRouter()
    routing = router.route_task(RoutingRequest(goal="Analyze scanned inspection report and draft approval note docx"))

    plan = planner.create_plan(
        goal="Analyze scanned inspection report and draft approval note docx",
        task_type=TaskType.DOCUMENT_ANALYSIS,
        routing=routing,
        uploaded_files=["inspection_p101.pdf"],
    )

    assert len(plan) == 4
    assert plan[0].tool_name == "document.ocr_parse"
    assert plan[1].tool_name == "knowledge.search"
    assert plan[2].tool_name is None  # Reasoning step
    assert plan[3].tool_name == "artifact.generate_docx"


def test_agent_verifier_validation():
    verifier = AgentVerifier()
    res = verifier.verify_execution(
        task_type="document_analysis",
        observations=["Obs 1", "Obs 2"],
        tool_results=[{"tool_name": "document.ocr_parse", "success": True}],
        generated_artifacts=[{"filename": "note.docx", "sha256_hash": "abcdef1234567890"}],
    )
    assert res.passed is True
    assert len(res.findings) >= 2


def test_agent_verifier_retry_recovery():
    verifier = AgentVerifier()
    # Tool initially failed on attempt 1, but recovered and passed on attempt 2 (self-repair)
    tool_results = [
        {"tool_name": "python.execute_sandbox", "success": False, "error": "AssertionError: math.isclose mismatch"},
        {"tool_name": "python.execute_sandbox", "success": True, "error": None},
    ]
    res = verifier.verify_execution(
        task_type="coding",
        observations=["Obs 1", "Obs 2"],
        tool_results=tool_results,
        generated_artifacts=[{"filename": "verified_script.py", "sha256_hash": "1234567890abcdef"}],
    )
    assert res.passed is True
    assert len(res.errors) == 0
    assert any("autonomously recovered" in f for f in res.findings)


@pytest.fixture
def mock_agent_service():
    mock_provider = MockProvider()
    registry = ModelRegistry()
    model_svc = ModelService(registry=registry)
    # Register mock provider for all models
    model_svc.register_provider(mock_provider)
    for m in registry.list_models(enabled_only=False):
        m.provider = "mock"
    return AgentService(model_service=model_svc)


@pytest.mark.asyncio
async def test_agent_orchestrator_inspection_workflow(mock_agent_service):
    state = mock_agent_service.create_task(
        goal="Analyze scanned inspection report for pump P-101 and draft Approval Note DOCX.",
        task_type=TaskType.DOCUMENT_ANALYSIS,
        uploaded_files=["inspection_p101.pdf"],
    )

    result_state = await mock_agent_service.execute_task(state.task_id, uploaded_files=["inspection_p101.pdf"])

    assert result_state.status == AgentStatus.COMPLETED
    assert len(result_state.plan) == 4
    assert len(result_state.tool_calls) >= 3
    assert len(result_state.generated_artifacts) >= 1
    assert result_state.verification_results is not None
    assert result_state.verification_results.passed is True


@pytest.mark.asyncio
async def test_agent_orchestrator_python_sandbox_workflow(mock_agent_service):
    state = mock_agent_service.create_task(
        goal="Write Python code to calculate pump efficiency and test in sandbox",
        task_type=TaskType.CODING,
    )

    result_state = await mock_agent_service.execute_task(state.task_id)

    assert result_state.status == AgentStatus.COMPLETED
    assert len(result_state.plan) == 3
    assert any(tc.tool_name == "python.execute_sandbox" for tc in result_state.tool_calls)
    assert result_state.verification_results.passed is True


def test_api_task_crud_and_execute(client):
    # 1. Create Task
    create_res = client.post("/api/v1/tasks", json={"goal": "Analyze inspection report and draft approval note docx"})
    assert create_res.status_code == 200
    task_data = create_res.json()
    task_id = task_data["task_id"]
    assert task_data["status"] == "pending"

    # 2. Get Task
    get_res = client.get(f"/api/v1/tasks/{task_id}")
    assert get_res.status_code == 200
    assert get_res.json()["task_id"] == task_id

    # 3. Execute Task
    exec_res = client.post(f"/api/v1/tasks/{task_id}/execute", json={"uploaded_files": ["pump_scan.pdf"]})
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "completed"
    assert len(exec_data["plan"]) >= 2
    assert len(exec_data["tool_calls"]) >= 2
