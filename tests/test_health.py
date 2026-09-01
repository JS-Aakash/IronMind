def test_root_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "IronMind" in data["app_name"]


def test_api_v1_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["sovereignty"]["cloud_egress"] == "BLOCKED"
    assert data["sovereignty"]["external_calls"] == 0
    assert data["services"]["model_gateway"] == "ready"
    assert data["services"]["sovereignty_monitor"] == "active"
