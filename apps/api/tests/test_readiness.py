"""Tests for the service readiness endpoint."""
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from app.db.session import get_db
from app.main import app


def test_ready_endpoint_success(client: TestClient):
    """Verify GET /api/v1/ready returns 200 OK and connected status when DB is healthy."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "ready",
        "database": "connected",
    }


def test_ready_endpoint_db_failure():
    """Verify GET /api/v1/ready returns 503 Service Unavailable when DB is unreachable."""
    def broken_get_db():
        mock_db = MagicMock()
        mock_db.execute.side_effect = OperationalError("connection refused", {}, None)
        try:
            yield mock_db
        finally:
            pass

    app.dependency_overrides[get_db] = broken_get_db
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        payload = response.json()
        assert payload == {
            "status": "not_ready",
            "database": "disconnected",
        }
        # Ensure no sensitive connection strings or credentials leaked
        assert "password" not in str(payload).lower()
        assert "127.0.0.1" not in str(payload)
    app.dependency_overrides.clear()


def test_health_remains_independent_of_db(client: TestClient):
    """Verify GET /api/v1/health still functions independently of DB status."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "mandatelens-api",
        "version": "0.1.0",
    }
