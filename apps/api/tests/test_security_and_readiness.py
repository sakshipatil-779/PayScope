"""Security, boundary, and production readiness tests for PayScope API."""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoints_do_not_leak_credentials(client: TestClient):
    """Verify health and readiness endpoints never expose sensitive database or Neo4j credentials."""
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "password" not in str(data).lower()
    assert "mandatelens_dev_password" not in str(data)

    resp_readiness = client.get("/api/v1/ready")
    assert resp_readiness.status_code in [200, 503]
    readiness_data = resp_readiness.json()
    assert "password" not in str(readiness_data).lower()
    assert "mandatelens_dev_password" not in str(readiness_data)


def test_graph_health_endpoint_masks_credentials(client: TestClient):
    """Verify graph health endpoint reports status without leaking auth credentials."""
    resp = client.get("/api/v1/graph/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "password" not in str(data).lower()
    assert "neo4j_password" not in str(data).lower()


def test_cors_headers_configured_properly(client: TestClient):
    """Verify CORS preflight handling conforms to configured origins."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    resp = client.options("/api/v1/health", headers=headers)
    assert resp.status_code in [200, 204]
    assert resp.headers.get("access-control-allow-origin") in ["http://localhost:3000", "*"]


def test_cors_origin_validator_logic():
    """Verify CORS origin string splitting supports comma-separated environment strings."""
    assert "https://payscope.vercel.app" in settings.BACKEND_CORS_ORIGINS
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS


def test_invalid_uuid_parameter_rejected_gracefully(client: TestClient):
    """Verify malformed UUID query parameters return standard HTTP 422 validation error."""
    resp = client.get("/api/v1/commitments/not-a-valid-uuid")
    assert resp.status_code == 422


def test_database_url_validator():
    """Verify database URL validator replaces postgres:// with postgresql+psycopg://."""
    result = settings.assemble_db_connection("postgres://user:pass@host:5432/db")
    assert result == "postgresql+psycopg://user:pass@host:5432/db"

    result_plain = settings.assemble_db_connection("postgresql://user:pass@host:5432/db")
    assert result_plain == "postgresql+psycopg://user:pass@host:5432/db"
