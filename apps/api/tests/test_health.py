"""Tests for the API health check endpoint."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check_status_and_payload():
    """Verify GET /api/v1/health returns 200 OK and expected JSON structure."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "status": "ok",
        "service": "mandatelens-api",
        "version": "0.1.0",
    }
