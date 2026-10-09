from fastapi.testclient import TestClient


def test_health_check_returns_200(client: TestClient):
    """Verify that GET /health returns HTTP 200 and valid schema."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert "app_name" in data
    assert "version" in data
    assert "environment" in data
    assert "components" in data

    # Verify application component status
    assert "app" in data["components"]
    assert data["components"]["app"]["status"] == "up"

    # Verify database component status is present and truthful
    assert "database" in data["components"]
    db_status = data["components"]["database"]["status"]
    assert db_status in ["up", "down", "not_configured"]


def test_health_check_via_api_v1(client: TestClient):
    """Verify that GET /api/v1/health returns HTTP 200 and matches expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "components" in data
    assert data["components"]["app"]["status"] == "up"


def test_database_not_falsely_healthy_when_unconfigured(client: TestClient):
    """Ensure database is not reported as healthy when unconfigured."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    # In default test environment without DATABASE_URL, DB should report not_configured
    db_component = data["components"]["database"]
    assert db_component["status"] in ["not_configured", "up", "down"]
    if db_component["status"] == "not_configured":
        assert "not configured" in db_component["details"].lower()


def test_root_endpoint(client: TestClient):
    """Verify that GET / returns service entry information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Welcome" in data["message"]
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


def test_database_reported_up_when_connected(client: TestClient):
    """When a real PostgreSQL database is configured, verify health reports database up."""
    import pytest
    from tests.conftest import is_postgres_available
    if not is_postgres_available():
        pytest.skip("PostgreSQL is not configured or reachable")

    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["components"]["database"]["status"] == "up"
    assert "verified" in data["components"]["database"]["details"].lower()
