import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from apps.backend.app.core.dependencies import get_model_gateway_service
from apps.backend.app.main import app
from packages.shared.models.enums import ModelRole, ModelStatus
from services.model_gateway.models import GenerationRequest, ModelDefinition
from services.model_gateway.providers.base import ModelProvider
from services.model_gateway.providers.mock import MockProvider
from services.model_gateway.providers.ollama import OllamaProvider
from services.model_gateway.registry import ModelRegistry
from services.model_gateway.service import ModelService


@pytest.fixture
def mock_model_service():
    """Create ModelService configured with MockProvider for all registered models."""
    registry = ModelRegistry()
    for m in registry.list_models(enabled_only=False):
        m.provider = "mock"
    return ModelService(registry=registry, default_provider="mock")


@pytest.fixture
def mock_client(mock_model_service):
    """Test client with mocked ModelService injected into FastAPI dependencies."""
    app.dependency_overrides[get_model_gateway_service] = lambda: mock_model_service
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_model_registry_defaults():
    registry = ModelRegistry()
    models = registry.list_models()
    assert len(models) >= 3

    # Check qwen3:8b
    qwen3 = registry.get_model("qwen3:8b")
    assert qwen3 is not None
    assert qwen3.role == ModelRole.REASONING
    assert "reasoning" in qwen3.capabilities

    # Check qwen2.5-coder:7b
    coder = registry.get_model("qwen2.5-coder:7b")
    assert coder is not None
    assert coder.role == ModelRole.CODING
    assert "python" in coder.capabilities

    # Check qwen2.5vl:7b
    vl = registry.get_model("qwen2.5vl:7b")
    assert vl is not None
    assert vl.role == ModelRole.VISION
    assert "vision" in vl.capabilities


def test_model_registry_find_by_role_and_capability():
    registry = ModelRegistry()
    reasoning_models = registry.find_by_role(ModelRole.REASONING)
    assert len(reasoning_models) >= 1

    vision_models = registry.find_by_capability("vision")
    assert len(vision_models) >= 1
    assert vision_models[0].name == "qwen2.5vl:7b"


@pytest.mark.asyncio
async def test_mock_provider_text_generation():
    provider = MockProvider()
    response = await provider.generate_text(
        model="qwen3:8b",
        prompt="Explain pump cavitation",
        system_prompt="Refinery SOP Assistant",
    )
    assert response.model == "qwen3:8b"
    assert response.provider == "mock"
    assert len(response.text) > 0
    assert response.total_tokens > 0


@pytest.mark.asyncio
async def test_mock_provider_structured_json():
    provider = MockProvider()
    response = await provider.generate_structured(
        model="qwen3:8b",
        prompt="Extract vibration metrics",
        schema_definition={"type": "object"},
    )
    assert response.structured_data is not None
    assert response.structured_data.get("status") == "success"


@pytest.mark.asyncio
async def test_mock_provider_image_analysis():
    provider = MockProvider()
    response = await provider.analyze_image(
        model="qwen2.5vl:7b",
        prompt="Identify equipment in P&ID",
        images=["sample_pid_base64_data"],
    )
    assert response.structured_data is not None
    assert "visual_elements_detected" in response.structured_data


@pytest.mark.asyncio
async def test_mock_provider_streaming():
    provider = MockProvider()
    chunks = []
    async for chunk in provider.stream(model="qwen3:8b", prompt="Stream test"):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert chunks[-1].is_done is True


@pytest.mark.asyncio
async def test_model_service_routing_with_mock():
    service = ModelService(default_provider="mock")
    for m in service.registry.list_models():
        m.provider = "mock"

    res = await service.generate_text(model="qwen3:8b", prompt="Test reasoning")
    assert res.provider == "mock"
    assert "qwen3:8b" in res.model


def test_ollama_provider_json_extraction():
    provider = OllamaProvider()

    # Raw json
    raw = '{"equipment": "Pump P-101", "status": "operational"}'
    parsed = provider._extract_json_from_text(raw)
    assert parsed == {"equipment": "Pump P-101", "status": "operational"}

    # Markdown json
    markdown = 'Here is the result:\n```json\n{"flow_rate": 150.5}\n```\nHope that helps!'
    parsed_md = provider._extract_json_from_text(markdown)
    assert parsed_md == {"flow_rate": 150.5}


def test_api_models_list_endpoint(mock_client):
    response = mock_client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert len(models) >= 3
    names = [m["id"] for m in models]
    assert any("qwen3" in name for name in names)


def test_api_models_health_endpoint(mock_client):
    response = mock_client.get("/api/v1/models/qwen3:8b/health")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "qwen3:8b"
    assert data["available"] is True


def test_api_models_test_qwen3_endpoint(mock_client):
    response = mock_client.post("/api/v1/models/test-qwen3?prompt=Calculate+head+loss")
    assert response.status_code == 200
    data = response.json()
    assert "model" in data
    assert data["model"] == "qwen3:8b"
    assert len(data["text"]) > 0


def test_api_models_generate_text_endpoint(mock_client):
    payload = {
        "prompt": "Review equipment logs for Pump P-101",
        "temperature": 0.2,
        "max_tokens": 100,
    }
    response = mock_client.post("/api/v1/models/qwen3:8b/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "qwen3:8b"
    assert "MockResponse" in data["text"]


def test_api_models_generate_structured_endpoint(mock_client):
    payload = {
        "prompt": "Extract structured inspection data",
        "json_format": True,
        "schema_definition": {"type": "object", "properties": {"vibration": {"type": "number"}}},
    }
    response = mock_client.post("/api/v1/models/qwen3:8b/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["structured_data"] is not None


def test_api_models_generate_image_endpoint(mock_client):
    payload = {
        "prompt": "Inspect P&ID valves",
        "images": ["dummy_base64_drawing_data"],
    }
    response = mock_client.post("/api/v1/models/qwen2.5vl:7b/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["structured_data"] is not None
    assert "visual_elements_detected" in data["structured_data"]
