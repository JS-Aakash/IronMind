from packages.shared.models.enums import ModelRole, SovereigntyStatus
from packages.shared.models.schemas import TaskCreateRequest
from services.agent import AgentService
from services.artifacts import ArtifactsService
from services.document_intelligence import DocumentIntelligenceService
from services.model_gateway import ModelGatewayService
from services.rag import RagService
from services.sandbox import SandboxService
from services.sovereignty import SovereigntyService


def test_model_gateway_initialization():
    gw = ModelGatewayService()
    models = gw.list_models()
    assert len(models) >= 3
    reasoning_model = gw.route_task_to_model(ModelRole.REASONING)
    assert reasoning_model is not None
    assert "qwen" in reasoning_model.name.lower()


def test_agent_service_task_creation():
    agent = AgentService()
    task = agent.create_task(TaskCreateRequest(goal="Analyze inspection report and draft approval note"))
    assert task.task_id.startswith("TASK_")
    assert task.status == "pending"


def test_rag_service_documents():
    rag = RagService()
    docs = rag.list_documents()
    assert len(docs) >= 1


def test_sovereignty_service_metrics():
    sov = SovereigntyService()
    metrics = sov.get_metrics()
    assert metrics.status == SovereigntyStatus.AIRGAPPED
    assert metrics.external_calls_count == 0
    assert metrics.egress_bytes == 0


def test_artifacts_service():
    art = ArtifactsService()
    items = art.list_artifacts()
    assert len(items) >= 1
    assert items[0].verified is True


def test_sandbox_service_status():
    sb = SandboxService()
    status = sb.get_status()
    assert status["network_isolated"] is True
    assert status["egress_blocked"] is True
