"""Tests for Unified Dashboard API endpoint."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
from fastapi.testclient import TestClient

from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.demo_user import DemoUser
from app.models.merchant import Merchant


def test_dashboard_summary_api(client: TestClient, db_session):
    user = DemoUser(workspace_key=f"ws_dash_{uuid.uuid4().hex[:6]}")
    db_session.add(user)
    db_session.commit()

    merchant = Merchant(canonical_name="Adobe Creative Cloud", category="Software")
    db_session.add(merchant)
    db_session.commit()

    now = datetime.now(timezone.utc)
    comm = Commitment(
        user_id=user.id,
        merchant_id=merchant.id,
        display_name="Adobe All Apps",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("4200.00"),
        first_seen_at=now - timedelta(days=60),
        last_seen_at=now,
    )
    db_session.add(comm)
    db_session.commit()

    # Add insight
    insight = CommitmentInsight(
        user_id=user.id,
        commitment_id=comm.id,
        insight_type="price_increase",
        severity="medium",
        status="open",
        title="Price Increased by 10%",
        summary="Monthly charge escalated from 3800 to 4200.",
        explanation="Observed 10% price escalation on recurring monthly cycle.",
        unique_fingerprint=f"fp_{uuid.uuid4().hex}",
        confidence_band="high",
        detected_at=now,
    )
    db_session.add(insight)
    db_session.commit()

    res = client.get(f"/api/v1/dashboard/summary?user_id={user.id}")
    assert res.status_code == 200
    data = res.json()

    assert "kpis" in data
    assert data["kpis"]["active_commitments_count"] == 1
    assert float(data["kpis"]["monthly_recurring_spend"]) == 4200.0
    assert float(data["kpis"]["annualized_recurring_spend"]) == 50400.0
    assert data["kpis"]["open_insights_count"] == 1

    assert "financial_overview" in data
    assert "top_commitments" in data
    assert len(data["top_commitments"]) == 1
    assert data["top_commitments"][0]["display_name"] == "Adobe All Apps"

    assert "recent_insights" in data
    assert len(data["recent_insights"]) == 1
    assert data["recent_insights"][0]["title"] == "Price Increased by 10%"
