import pytest
from fastapi.testclient import TestClient

from apps.backend.app.main import app
from services.sovereignty.guardrails import (
    CloudProviderBlocker,
    NetworkEgressInterceptor,
    SovereigntyViolationError,
)
from services.sovereignty.models import SovereigntyStatusResponse
from services.sovereignty.service import SovereigntyService


@pytest.fixture
def sovereignty_service():
    return SovereigntyService()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------
# 1. Sovereignty Status Structure & Metric Distinctions
# ---------------------------------------------------------

def test_sovereignty_status_structure(sovereignty_service):
    status = sovereignty_service.get_sovereignty_status()

    assert isinstance(status, SovereigntyStatusResponse)
    assert status.mode == "air_gapped"
    assert status.internet_access == "blocked"
    assert status.external_api_calls == 0
    assert status.cloud_llm_calls == 0
    assert status.data_egress_bytes == 0
    assert status.local_model_calls >= 1

    # Check three-tier measurement breakdown
    breakdown = status.measurement_breakdown
    assert breakdown.directly_measured.socket_egress_bytes == 0
    assert breakdown.directly_measured.dns_queries_attempted == 0
    assert breakdown.derived_from_application_logs.cloud_llm_calls == 0
    assert breakdown.derived_from_application_logs.local_model_calls >= 1
    assert breakdown.enforced_by_configuration.cloud_providers_blocked is True
    assert "127.0.0.1" in breakdown.enforced_by_configuration.allowed_hosts


# ---------------------------------------------------------
# 2. Cloud Provider & Remote URL Guardrails
# ---------------------------------------------------------

def test_cloud_provider_blocker():
    # Forbidden cloud AI providers
    forbidden_providers = ["openai", "anthropic", "gemini", "bedrock", "cohere", "azure.openai"]
    for prov in forbidden_providers:
        with pytest.raises(SovereigntyViolationError):
            CloudProviderBlocker.validate_provider(prov)

    # Authorized local on-premise models
    assert CloudProviderBlocker.validate_provider("ollama") is True
    assert CloudProviderBlocker.validate_provider("qwen3:8b", endpoint_url="http://127.0.0.1:11434") is True

    # Remote non-loopback URL should be blocked
    with pytest.raises(SovereigntyViolationError):
        CloudProviderBlocker.validate_provider("ollama", endpoint_url="http://192.168.1.100:11434")


# ---------------------------------------------------------
# 3. Network Egress Interceptor
# ---------------------------------------------------------

def test_network_egress_interceptor():
    # Loopback targets are permitted
    assert NetworkEgressInterceptor.is_request_allowed("http://127.0.0.1:11434") is True
    assert NetworkEgressInterceptor.is_request_allowed("http://localhost:8000") is True

    # Public external targets are blocked
    assert NetworkEgressInterceptor.is_request_allowed("https://api.openai.com/v1") is False
    assert NetworkEgressInterceptor.is_request_allowed("https://api.anthropic.com") is False
    assert NetworkEgressInterceptor.is_request_allowed("http://8.8.8.8:53") is False


# ---------------------------------------------------------
# 4. Live Air-Gap Verification Probe
# ---------------------------------------------------------

def test_verify_airgap_probe(sovereignty_service):
    res = sovereignty_service.verify_airgap_status()
    assert res["status"] == "verified_airgapped"
    assert res["loopback_isolated"] is True
    assert res["cloud_providers_blocked"] is True
    assert res["external_egress_bytes"] == 0


# ---------------------------------------------------------
# 5. REST API Endpoint Tests for Sovereignty Subsystem
# ---------------------------------------------------------

def test_api_sovereignty_endpoints(client):
    # 1. GET /api/v1/sovereignty/status
    res = client.get("/api/v1/sovereignty/status")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "air_gapped"
    assert data["internet_access"] == "blocked"
    assert data["external_api_calls"] == 0
    assert data["cloud_llm_calls"] == 0
    assert data["data_egress_bytes"] == 0
    assert "measurement_breakdown" in data

    # 2. GET /api/v1/sovereignty/metrics
    metrics_res = client.get("/api/v1/sovereignty/metrics")
    assert metrics_res.status_code == 200
    assert metrics_res.json()["egress_bytes"] == 0

    # 3. GET /api/v1/sovereignty/network-audit
    audit_res = client.get("/api/v1/sovereignty/network-audit")
    assert audit_res.status_code == 200
    assert audit_res.json()["zero_egress_verified"] is True

    # 4. POST /api/v1/sovereignty/verify-airgap
    probe_res = client.post("/api/v1/sovereignty/verify-airgap")
    assert probe_res.status_code == 200
    assert probe_res.json()["status"] == "verified_airgapped"
