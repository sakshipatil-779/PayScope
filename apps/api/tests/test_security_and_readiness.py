"""Security, boundary, and production readiness tests for PayScope API."""
import uuid
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import get_db
import app.api.v1.routes.dashboard as dashboard_module
from app.api.v1.routes.dashboard import (
    DashboardSummaryResponse,
    DashboardKPIs,
    DashboardFinancialOverview,
)


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
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert resp.headers.get("access-control-allow-credentials") == "true"


def test_cors_production_vercel_preflight_and_get(client: TestClient):
    """Verify production Vercel frontend origin passes CORS preflight OPTIONS and GET on health and dashboard."""
    origin = "https://pay-scope-lake.vercel.app"

    # 1. Preflight on /api/v1/health
    options_health = client.options(
        "/api/v1/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert options_health.status_code in [200, 204]
    assert options_health.headers.get("access-control-allow-origin") == origin
    assert options_health.headers.get("access-control-allow-credentials") == "true"

    # 2. GET on /api/v1/health
    get_health = client.get("/api/v1/health", headers={"Origin": origin})
    assert get_health.status_code == 200
    assert get_health.headers.get("access-control-allow-origin") == origin
    assert get_health.headers.get("access-control-allow-credentials") == "true"

    # 3. Preflight on /api/v1/dashboard/summary
    options_dash = client.options(
        "/api/v1/dashboard/summary",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert options_dash.status_code in [200, 204]
    assert options_dash.headers.get("access-control-allow-origin") == origin
    assert options_dash.headers.get("access-control-allow-credentials") == "true"

    # 4. GET on /api/v1/dashboard/summary with mock db dependency
    mock_summary = DashboardSummaryResponse(
        kpis=DashboardKPIs(
            active_commitments_count=22,
            monthly_recurring_spend="36817.03",
            annualized_recurring_spend="441804.40",
            open_insights_count=51,
            potential_annual_savings="441804.40",
            cancellations_attention_count=0,
        ),
        financial_overview=DashboardFinancialOverview(
            monthly_recurring_spend="36817.03",
            annualized_recurring_spend="441804.40",
            upcoming_month_expected="26469.26",
            candidate_annual_cost="10788.00",
            historical_months=["Last 30 Days"],
            historical_amounts=["13829.97"],
        ),
        top_commitments=[],
        category_distribution={"Software": 4200.0},
        recent_insights=[],
        insight_type_counts={"price_increase": 2},
        cancellation_summary={"total": 0},
        merchant_review_pending=0,
        canonical_merchants_count=22,
    )

    app.dependency_overrides[get_db] = lambda: MagicMock()
    orig_fn = dashboard_module.get_dashboard_summary
    try:
        dashboard_module.get_dashboard_summary = lambda *args, **kwargs: mock_summary
        get_dash = client.get("/api/v1/dashboard/summary", headers={"Origin": origin})
        assert get_dash.status_code == 200
        assert get_dash.headers.get("access-control-allow-origin") == origin
        assert get_dash.headers.get("access-control-allow-credentials") == "true"
        dash_json = get_dash.json()
        assert "kpis" in dash_json
        assert dash_json["kpis"]["active_commitments_count"] == 22
    finally:
        dashboard_module.get_dashboard_summary = orig_fn
        app.dependency_overrides.clear()


def test_cors_preview_vercel_origin_supported(client: TestClient):
    """Verify preview deployments on Vercel match regex and receive CORS headers."""
    preview_origin = "https://pay-scope-lake-git-main-sakshipatil.vercel.app"
    resp = client.options(
        "/api/v1/health",
        headers={
            "Origin": preview_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code in [200, 204]
    assert resp.headers.get("access-control-allow-origin") == preview_origin


def test_cors_disallowed_origin_rejected(client: TestClient):
    """Verify unapproved origins are blocked by CORS middleware."""
    disallowed = "https://unauthorized-malicious-domain.com"
    resp = client.options(
        "/api/v1/health",
        headers={
            "Origin": disallowed,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 400
    assert resp.headers.get("access-control-allow-origin") is None


def test_cors_origin_validator_logic():
    """Verify CORS origin string splitting supports comma strings, JSON arrays, and always retains dev/prod origins."""
    assert "https://pay-scope-lake.vercel.app" in settings.BACKEND_CORS_ORIGINS
    assert "https://payscope.vercel.app" in settings.BACKEND_CORS_ORIGINS
    assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS

    # Comma-separated with trailing slashes
    parsed = settings.assemble_cors_origins("https://custom.vercel.app/, http://127.0.0.1:4000")
    assert "https://custom.vercel.app" in parsed
    assert "http://127.0.0.1:4000" in parsed
    assert "https://pay-scope-lake.vercel.app" in parsed
    assert "http://localhost:3000" in parsed

    # JSON array representation
    parsed_json = settings.assemble_cors_origins('["https://extra.vercel.app/"]')
    assert "https://extra.vercel.app" in parsed_json
    assert "https://pay-scope-lake.vercel.app" in parsed_json

    # Wildcard filter - must never allow "*" with credentials enabled
    parsed_wildcard = settings.assemble_cors_origins("*")
    assert "*" not in parsed_wildcard
    assert "https://pay-scope-lake.vercel.app" in parsed_wildcard


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
