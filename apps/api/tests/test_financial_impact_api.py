"""Integration and API tests for Phase 7 Financial Impact and Savings Intelligence endpoints."""
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.demo_user import DemoUser
from app.models.price_event import PriceEvent
from app.models.savings_scenario import SavingsScenario


@pytest.fixture
def setup_financial_data(db_session: Session):
    """Set up test user with confirmed commitments, price event, and insights."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    # Confirmed active commitment
    c1 = Commitment(
        user_id=user.id,
        display_name="CloudDesk Pro",
        commitment_type="productivity",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("999.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    # Candidate commitment
    c2 = Commitment(
        user_id=user.id,
        display_name="Suraksha General Insurance",
        commitment_type="insurance",
        cadence="annual",
        status="candidate",
        confidence_band="needs_review",
        representative_amount=Decimal("15000.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    # Price increase event on c1
    pe = PriceEvent(
        commitment_id=c1.id,
        event_type="amount_increase",
        previous_amount=Decimal("799.00"),
        new_amount=Decimal("999.00"),
        currency="INR",
        absolute_change=Decimal("200.00"),
        percentage_change=Decimal("25.0"),
        effective_or_detected_at=datetime.now(timezone.utc),
        confidence_band="high",
        detector_version="v1.0",
    )
    db_session.add(pe)
    db_session.commit()

    insight = CommitmentInsight(
        user_id=user.id,
        commitment_id=c1.id,
        insight_type="price_increase",
        severity="medium",
        title="CloudDesk Pro increased by ₹200.00",
        summary="Price increase detected",
        explanation="Consecutive higher charges detected",
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"api_test_pe_{uuid.uuid4().hex}",
    )
    db_session.add(insight)
    db_session.commit()

    return {"user": user, "c1": c1, "c2": c2, "pe": pe, "insight": insight}


def test_api_financial_summary(client: TestClient, setup_financial_data):
    """Test GET /api/v1/financial-impact/summary."""
    user = setup_financial_data["user"]
    res = client.get(f"/api/v1/financial-impact/summary?user_id={user.id}")
    assert res.status_code == 200
    data = res.json()
    assert float(data["monthly_recurring_spend"]) == 999.0
    assert float(data["annualized_recurring_spend"]) == 11988.0
    assert data["total_confirmed_commitments"] == 1
    assert float(data["potential_candidate_annual_cost"]) == 15000.0
    assert data["total_candidate_commitments"] == 1


def test_api_commitment_costs(client: TestClient, setup_financial_data):
    """Test GET /api/v1/financial-impact/commitments."""
    user = setup_financial_data["user"]
    res = client.get(f"/api/v1/financial-impact/commitments?user_id={user.id}")
    assert res.status_code == 200
    items = res.json()
    assert len(items) == 2

    # Confirmed only filter
    res_conf = client.get(f"/api/v1/financial-impact/commitments?user_id={user.id}&confirmed_only=true")
    assert res_conf.status_code == 200
    conf_items = res_conf.json()
    assert len(conf_items) == 1
    assert conf_items[0]["display_name"] == "CloudDesk Pro"


def test_api_historical_spend(client: TestClient, setup_financial_data):
    """Test GET /api/v1/financial-impact/history."""
    user = setup_financial_data["user"]
    res = client.get(f"/api/v1/financial-impact/history?user_id={user.id}")
    assert res.status_code == 200
    data = res.json()
    assert "periods" in data
    assert len(data["periods"]) == 5
    assert "monthly_timeline" in data


def test_api_category_and_merchant_breakdowns(client: TestClient, setup_financial_data):
    """Test GET /api/v1/financial-impact/categories and /merchants."""
    user = setup_financial_data["user"]
    res_cat = client.get(f"/api/v1/financial-impact/categories?user_id={user.id}")
    assert res_cat.status_code == 200
    cats = res_cat.json()
    assert len(cats) >= 1

    res_m = client.get(f"/api/v1/financial-impact/merchants?user_id={user.id}")
    assert res_m.status_code == 200
    merchants = res_m.json()
    assert len(merchants) >= 1


def test_api_upcoming_expenditure(client: TestClient, setup_financial_data):
    """Test GET /api/v1/financial-impact/upcoming."""
    user = setup_financial_data["user"]
    res = client.get(f"/api/v1/financial-impact/upcoming?user_id={user.id}")
    assert res.status_code == 200
    data = res.json()
    assert "total_upcoming_30d" in data
    assert "items" in data


def test_api_savings_opportunities_and_summary(client: TestClient, setup_financial_data):
    """Test GET /api/v1/savings/opportunities and /summary."""
    user = setup_financial_data["user"]
    res_opps = client.get(f"/api/v1/savings/opportunities?user_id={user.id}")
    assert res_opps.status_code == 200
    opps = res_opps.json()
    assert len(opps) == 1
    assert opps[0]["opportunity_type"] == "PRICE_INCREASE"
    assert opps[0]["classification"] == "POTENTIAL"

    res_sum = client.get(f"/api/v1/savings/summary?user_id={user.id}")
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert float(sum_data["price_increase_savings"]) == 2400.0


def test_api_savings_what_if_calculation(client: TestClient, setup_financial_data):
    """Test POST /api/v1/savings/calculate."""
    user = setup_financial_data["user"]
    pe = setup_financial_data["pe"]
    opp_id = f"opp_price_{pe.id}"

    payload = {"selected_opportunity_ids": [opp_id]}
    res = client.post(f"/api/v1/savings/calculate?user_id={user.id}", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert float(data["baseline_annual_cost"]) == 11988.0
    assert float(data["selected_annual_savings"]) == 2400.0
    assert float(data["projected_annual_cost"]) == 9588.0
    assert float(data["selected_monthly_savings"]) == 200.0
    assert data["selected_count"] == 1


def test_api_savings_scenario_crud(client: TestClient, setup_financial_data):
    """Test POST, GET, PATCH, DELETE /api/v1/savings/scenarios."""
    user = setup_financial_data["user"]
    pe = setup_financial_data["pe"]
    opp_id = f"opp_price_{pe.id}"

    # 1. Create scenario
    create_payload = {
        "name": "CloudDesk Optimization",
        "description": "Negotiate or revert CloudDesk price increase",
        "selected_opportunity_ids": [opp_id],
    }
    res_create = client.post(f"/api/v1/savings/scenarios?user_id={user.id}", json=create_payload)
    assert res_create.status_code == 201
    created = res_create.json()
    scenario_id = created["id"]
    assert created["name"] == "CloudDesk Optimization"
    assert float(created["annual_savings"]) == 2400.0

    # 2. List scenarios
    res_list = client.get(f"/api/v1/savings/scenarios?user_id={user.id}")
    assert res_list.status_code == 200
    scenarios = res_list.json()
    assert len(scenarios) >= 1
    assert any(s["id"] == scenario_id for s in scenarios)

    # 3. Get single scenario
    res_get = client.get(f"/api/v1/savings/scenarios/{scenario_id}?user_id={user.id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == scenario_id

    # 4. Patch scenario
    patch_payload = {
        "name": "CloudDesk Renegotiation Plan",
        "description": "Updated scenario notes",
    }
    res_patch = client.patch(f"/api/v1/savings/scenarios/{scenario_id}?user_id={user.id}", json=patch_payload)
    assert res_patch.status_code == 200
    assert res_patch.json()["name"] == "CloudDesk Renegotiation Plan"

    # 5. Delete scenario
    res_del = client.delete(f"/api/v1/savings/scenarios/{scenario_id}?user_id={user.id}")
    assert res_del.status_code == 204

    # 6. Verify 404 after deletion
    res_get_del = client.get(f"/api/v1/savings/scenarios/{scenario_id}?user_id={user.id}")
    assert res_get_del.status_code == 404
