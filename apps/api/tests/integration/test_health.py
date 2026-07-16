from fastapi.testclient import TestClient


def test_health_and_readiness(api_client: TestClient) -> None:
    liveness = api_client.get("/health", headers={"X-Request-ID": "test-request"})
    readiness = api_client.get("/ready")

    assert liveness.status_code == 200
    assert liveness.json()["status"] == "ok"
    assert liveness.headers["X-Request-ID"] == "test-request"
    assert readiness.status_code == 200
    assert readiness.json() == {"status": "ok", "database": "available"}


def test_integration_health_reports_modes(api_client: TestClient) -> None:
    response = api_client.get("/api/integrations/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert {component["name"] for component in payload["components"]} == {
        "database",
        "crm",
        "documents",
        "embeddings",
    }
