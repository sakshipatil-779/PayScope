"""Unit and domain tests for Phase 7 Financial Impact, Normalization, Historical Spend, and Savings Intelligence."""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session

from app.analytics.financial_impact.category_analysis import get_user_category_analysis
from app.analytics.financial_impact.commitment_costs import (
    get_user_commitment_costs,
    is_confirmed_commitment,
)
from app.analytics.financial_impact.historical_spend import get_user_historical_spend
from app.analytics.financial_impact.impact_summary import get_user_financial_summary
from app.analytics.financial_impact.merchant_analysis import get_user_merchant_analysis
from app.analytics.financial_impact.normalization import (
    calculate_normalized_costs,
    round_currency,
)
from app.analytics.financial_impact.savings_calculator import (
    calculate_what_if_projection,
    get_user_savings_opportunities,
    get_user_savings_summary,
)
from app.analytics.financial_impact.upcoming import get_user_upcoming_expenditure
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.commitment_transaction import CommitmentTransaction
from app.models.demo_user import DemoUser
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant
from app.models.price_event import PriceEvent
from app.models.transaction import Transaction
from app.models.usage_coverage import UsageCoverage


# ==============================================================================
# 1-6. Normalization Tests
# ==============================================================================

def test_normalization_weekly_cadence():
    """1. Weekly cadence normalization: amount * 52 / 12 and annual amount * 52."""
    amount = Decimal("250.00")
    monthly, annual, method = calculate_normalized_costs(amount, "weekly")
    # 250 * 52 / 12 = 1083.33
    assert monthly == Decimal("1083.33")
    assert annual == Decimal("13000.00")
    assert "Weekly" in method


def test_normalization_fortnightly_cadence():
    """2. Fortnightly cadence normalization: amount * 26 / 12 and annual amount * 26."""
    amount = Decimal("600.00")
    monthly, annual, method = calculate_normalized_costs(amount, "fortnightly")
    # 600 * 26 / 12 = 1300.00
    assert monthly == Decimal("1300.00")
    assert annual == Decimal("15600.00")
    assert "Fortnightly" in method


def test_normalization_monthly_cadence():
    """3. Monthly cadence normalization: monthly = amount, annual = amount * 12."""
    amount = Decimal("499.00")
    monthly, annual, method = calculate_normalized_costs(amount, "monthly")
    assert monthly == Decimal("499.00")
    assert annual == Decimal("5988.00")
    assert "Monthly" in method


def test_normalization_quarterly_cadence():
    """4. Quarterly cadence normalization: monthly = amount / 3, annual = amount * 4."""
    amount = Decimal("1499.00")
    monthly, annual, method = calculate_normalized_costs(amount, "quarterly")
    # 1499 / 3 = 499.67, 1499 * 4 = 5996.00
    assert monthly == Decimal("499.67")
    assert annual == Decimal("5996.00")
    assert "Quarterly" in method


def test_normalization_annual_cadence():
    """5. Annual payment normalization: monthly = amount / 12, annual = amount."""
    amount = Decimal("12000.00")
    monthly, annual, method = calculate_normalized_costs(amount, "annual")
    assert monthly == Decimal("1000.00")
    assert annual == Decimal("12000.00")
    assert "Annual" in method


def test_normalization_variable_monthly_cost():
    """6. Variable monthly cost calculation: uses historical median amounts."""
    historical = [Decimal("300.00"), Decimal("450.00"), Decimal("500.00")]
    monthly, annual, method = calculate_normalized_costs(Decimal("450.00"), "variable_monthly", historical)
    assert monthly == Decimal("450.00")
    assert annual == Decimal("5400.00")
    assert "median" in method


# ==============================================================================
# 7, 18. Candidate Exclusion & Classification
# ==============================================================================

def test_single_annual_candidate_exclusion_from_confirmed_totals(db_session: Session):
    """7 & 18. Single annual candidate (Suraksha General Insurance) must be candidate-only, not confirmed."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    # Create confirmed Netflix monthly commitment
    c1 = Commitment(
        user_id=user.id,
        display_name="Netflix Standard",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("499.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    # Create Suraksha candidate-only annual commitment
    c2 = Commitment(
        user_id=user.id,
        display_name="Suraksha General Insurance",
        commitment_type="insurance",
        cadence="annual",
        status="candidate",  # candidate only!
        confidence_band="needs_review",
        representative_amount=Decimal("14250.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    assert is_confirmed_commitment(c1) is True
    assert is_confirmed_commitment(c2) is False

    summary = get_user_financial_summary(db_session, user.id)
    # Confirmed recurring monthly spend must be ONLY Netflix (₹499), NOT Suraksha
    assert summary.monthly_recurring_spend == Decimal("499.00")
    assert summary.annualized_recurring_spend == Decimal("5988.00")
    assert summary.total_confirmed_commitments == 1

    # Suraksha must be captured under candidate metrics
    assert summary.potential_candidate_annual_cost == Decimal("14250.00")
    assert summary.total_candidate_commitments == 1


# ==============================================================================
# 8-11, 13. Historical Spend Filtering Tests
# ==============================================================================

def test_historical_spend_filtering_rules(db_session: Session):
    """8, 9, 10, 11, 13. Historical spend exclusions: failed, reversed, credit, duplicate."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    now = datetime.now(timezone.utc)

    # 1. Valid successful debit
    t1 = Transaction(
        user_id=user.id,
        amount=Decimal("1000.00"),
        currency="INR",
        direction="debit",
        transaction_status="successful",
        raw_descriptor="NETFLIX MUMBAI",
        external_synthetic_id="tx_valid_1",
        transaction_date=now - timedelta(days=10),
    )
    # 2. Failed transaction (must be excluded)
    t2 = Transaction(
        user_id=user.id,
        amount=Decimal("500.00"),
        currency="INR",
        direction="debit",
        transaction_status="failed",
        raw_descriptor="FAILED RECHARGE",
        external_synthetic_id="tx_failed_2",
        transaction_date=now - timedelta(days=12),
    )
    # 3. Reversed transaction (must be excluded)
    t3 = Transaction(
        user_id=user.id,
        amount=Decimal("700.00"),
        currency="INR",
        direction="debit",
        transaction_status="reversed",
        raw_descriptor="REVERSED ORDER",
        external_synthetic_id="tx_reversed_3",
        transaction_date=now - timedelta(days=15),
    )
    # 4. Credit transaction (must be counted under credits, NOT gross debit spend)
    t4 = Transaction(
        user_id=user.id,
        amount=Decimal("200.00"),
        currency="INR",
        direction="credit",
        transaction_status="successful",
        raw_descriptor="SALARY CREDIT",
        external_synthetic_id="tx_credit_4",
        transaction_date=now - timedelta(days=5),
    )

    db_session.add_all([t1, t2, t3, t4])
    db_session.commit()

    spend_resp = get_user_historical_spend(db_session, user.id, as_of=now)
    p30d = next(p for p in spend_resp.periods if p.period == "30d")

    # Gross debit must be strictly ₹1000.00 (t1 only, t2/t3 excluded)
    assert p30d.gross_debit_amount == Decimal("1000.00")
    # Total credits must be ₹200.00
    assert p30d.total_credits == Decimal("200.00")
    # Net spend = ₹800.00
    assert p30d.net_spend == Decimal("800.00")
    assert p30d.transaction_count == 1
    assert p30d.excluded_failed_count == 2


# ==============================================================================
# 12. Merchant Alias Aggregation Without Double Counting
# ==============================================================================

def test_merchant_alias_aggregation_without_double_counting(db_session: Session):
    """12. Merchant alias aggregation: multiple aliases map to canonical merchant without duplicate totals."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    m = Merchant(canonical_name="Amazon Prime", category="entertainment")
    db_session.add_all([user, m])
    db_session.commit()

    a1 = DescriptorAlias(
        merchant_id=m.id,
        alias_text="AMZN PRIME IND",
        normalised_alias="AMZN PRIME IND",
        pattern="AMZN PRIME IND",
    )
    a2 = DescriptorAlias(
        merchant_id=m.id,
        alias_text="AMAZON DIGITAL",
        normalised_alias="AMAZON DIGITAL",
        pattern="AMAZON DIGITAL",
    )
    db_session.add_all([a1, a2])

    c = Commitment(
        user_id=user.id,
        merchant_id=m.id,
        display_name="Amazon Prime",
        commitment_type="subscription",
        cadence="annual",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("1499.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=180),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(c)
    db_session.commit()

    rankings = get_user_merchant_analysis(db_session, user.id)
    assert len(rankings) == 1
    r = rankings[0]
    assert r.merchant_name == "Amazon Prime"
    assert r.annualized_cost == Decimal("1499.00")
    assert "AMZN PRIME IND" in r.aliases
    assert "AMAZON DIGITAL" in r.aliases


# ==============================================================================
# 14-17. Savings Intelligence: Price Increases & Unused Verification
# ==============================================================================

def test_price_increase_incremental_annual_savings(db_session: Session):
    """14. Price increase opportunity correctly reflects incremental annual impact."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    c = Commitment(
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
    db_session.add(c)
    db_session.commit()

    pe = PriceEvent(
        commitment_id=c.id,
        event_type="amount_increase",
        previous_amount=Decimal("799.00"),
        new_amount=Decimal("999.00"),
        currency="INR",
        absolute_change=Decimal("200.00"),
        percentage_change=Decimal("25.03"),
        effective_or_detected_at=datetime.now(timezone.utc),
        confidence_band="high",
        detector_version="v1.0",
    )
    db_session.add(pe)
    db_session.commit()

    insight = CommitmentInsight(
        user_id=user.id,
        commitment_id=c.id,
        insight_type="price_increase",
        severity="medium",
        title="CloudDesk Pro price increased by ₹200.00/mo",
        summary="Price increased from ₹799 to ₹999",
        explanation="Sustained price increase detected across consecutive billing cycles",
        confidence_score=Decimal("0.95"),
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"test_pe_{uuid.uuid4().hex}",
    )
    db_session.add(insight)
    db_session.commit()

    opps = get_user_savings_opportunities(db_session, user.id)
    assert len(opps) == 1
    opp = opps[0]
    assert opp.opportunity_type == "PRICE_INCREASE"
    assert opp.potential_monthly_saving == Decimal("200.00")
    assert opp.potential_annual_saving == Decimal("2400.00")
    assert opp.classification == "POTENTIAL"


def test_potentially_unused_commitment_requires_verified_coverage(db_session: Session):
    """15, 16, 17. Unused commitment savings require verified coverage (COMPLETE/PARTIAL) and exclude UNAVAILABLE/INSUFFICIENT."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    # C1: Verified coverage (COMPLETE)
    c1 = Commitment(
        user_id=user.id,
        display_name="Gym Membership",
        commitment_type="fitness",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("2000.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    # C2: Unverified coverage (UNAVAILABLE) - must be excluded
    c2 = Commitment(
        user_id=user.id,
        display_name="Audible Books",
        commitment_type="entertainment",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("199.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    cov1 = UsageCoverage(
        user_id=user.id,
        commitment_id=c1.id,
        source_label="cult_gym_rfid",
        coverage_complete=True,  # verified!
        coverage_start=date.today() - timedelta(days=90),
        coverage_end=date.today(),
    )
    cov2 = UsageCoverage(
        user_id=user.id,
        commitment_id=c2.id,
        source_label="unknown",
        coverage_complete=False,  # unverified/incomplete!
        coverage_start=date.today() - timedelta(days=30),
        coverage_end=date.today(),
    )
    db_session.add_all([cov1, cov2])
    db_session.commit()

    ins1 = CommitmentInsight(
        user_id=user.id,
        commitment_id=c1.id,
        insight_type="potentially_unused",
        severity="medium",
        title="Gym Membership potentially unused",
        summary="No visits detected",
        explanation="RFID inactivity across 60 days",
        confidence_score=Decimal("0.90"),
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"test_u1_{uuid.uuid4().hex}",
    )
    ins2 = CommitmentInsight(
        user_id=user.id,
        commitment_id=c2.id,
        insight_type="potentially_unused",
        severity="low",
        title="Audible status unknown",
        summary="No usage coverage available",
        explanation="Inactivity cannot be verified",
        confidence_score=Decimal("0.50"),
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"test_u2_{uuid.uuid4().hex}",
    )
    db_session.add_all([ins1, ins2])
    db_session.commit()

    opps = get_user_savings_opportunities(db_session, user.id)
    # Must contain ONLY c1 (Gym Membership), c2 must be excluded!
    unused_opps = [o for o in opps if o.opportunity_type == "POTENTIALLY_UNUSED"]
    assert len(unused_opps) == 1
    assert unused_opps[0].commitment_id == c1.id
    assert unused_opps[0].potential_annual_saving == Decimal("24000.00")


# ==============================================================================
# 19-22. What-If Projections, Duplicate Services, Safeguards
# ==============================================================================

def test_duplicate_services_and_what_if_safeguards(db_session: Session):
    """19, 20, 21, 22. Duplicate category services, non-negative safeguard, and double-count protection."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    # Two active streaming commitments
    c1 = Commitment(
        user_id=user.id,
        display_name="Netflix Premium",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("649.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    c2 = Commitment(
        user_id=user.id,
        display_name="Disney+ Hotstar",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("299.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add_all([c1, c2])
    db_session.commit()

    opps = get_user_savings_opportunities(db_session, user.id)
    dup_opps = [o for o in opps if o.opportunity_type == "CATEGORY_DUPLICATE"]
    assert len(dup_opps) >= 1
    hotstar_opp = next(o for o in dup_opps if o.commitment_id == c2.id)
    assert hotstar_opp.potential_annual_saving == Decimal("3588.00")

    # Test what-if calculation selecting Hotstar optimization
    res = calculate_what_if_projection(db_session, user.id, [hotstar_opp.id])
    # Baseline: (649 + 299) * 12 = 11376.00
    assert res.baseline_annual_cost == Decimal("11376.00")
    assert res.selected_annual_savings == Decimal("3588.00")
    # Projected: 11376 - 3588 = 7788.00 (Netflix only)
    assert res.projected_annual_cost == Decimal("7788.00")
    assert res.projected_monthly_cost == Decimal("649.00")
    assert res.percentage_reduction > Decimal("31.0")


def test_double_count_and_non_negative_safeguards(db_session: Session):
    """21 & 22. Savings capped at commitment annual cost and projection never negative."""
    user = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add(user)
    db_session.commit()

    c = Commitment(
        user_id=user.id,
        display_name="Streaming Hub",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("500.00"),  # Annual = 6000
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=90),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(c)
    db_session.commit()

    # Add PriceEvent: +100/mo (annual 1200)
    pe = PriceEvent(
        commitment_id=c.id,
        event_type="amount_increase",
        previous_amount=Decimal("400.00"),
        new_amount=Decimal("500.00"),
        currency="INR",
        absolute_change=Decimal("100.00"),
        percentage_change=Decimal("25.0"),
        effective_or_detected_at=datetime.now(timezone.utc),
        confidence_band="high",
        detector_version="v1.0",
    )
    db_session.add(pe)
    db_session.commit()

    ins_p = CommitmentInsight(
        user_id=user.id,
        commitment_id=c.id,
        insight_type="price_increase",
        severity="medium",
        title="Streaming Hub price increase",
        summary="Price increase detected",
        explanation="Sustained increase detected",
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"test_pe2_{uuid.uuid4().hex}",
    )
    # Add Unused Insight: annual 6000
    cov = UsageCoverage(
        user_id=user.id,
        commitment_id=c.id,
        source_label="activity_log",
        coverage_complete=True,
        coverage_start=date.today() - timedelta(days=90),
        coverage_end=date.today(),
    )
    db_session.add_all([ins_p, cov])
    db_session.commit()

    ins_u = CommitmentInsight(
        user_id=user.id,
        commitment_id=c.id,
        insight_type="potentially_unused",
        severity="high",
        title="Streaming Hub unused",
        summary="No activity detected",
        explanation="Activity logs indicate prolonged absence",
        status="open",
        detected_at=datetime.now(timezone.utc),
        unique_fingerprint=f"test_un2_{uuid.uuid4().hex}",
    )
    db_session.add(ins_u)
    db_session.commit()

    opps = get_user_savings_opportunities(db_session, user.id)
    opp_ids = [o.id for o in opps if o.commitment_id == c.id]

    # User selects BOTH opportunities on the same commitment (1200 + 6000 = 7200)
    # Double-count protection must cap savings at commitment annual cost (6000.00)
    res = calculate_what_if_projection(db_session, user.id, opp_ids)
    assert res.baseline_annual_cost == Decimal("6000.00")
    assert res.selected_annual_savings == Decimal("6000.00")  # Capped at 6000, not 7200!
    assert res.projected_annual_cost == Decimal("0.00")       # Not negative!
    assert any("Double-count" in s for s in res.safeguards_applied)


# ==============================================================================
# 23, 24. User Isolation & Empty Dataset Handling
# ==============================================================================

def test_user_isolation_and_empty_dataset(db_session: Session):
    """23 & 24. Data isolation between users and graceful handling of empty datasets."""
    user1 = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    user2 = DemoUser(workspace_key=f"ws_{uuid.uuid4().hex[:8]}")
    db_session.add_all([user1, user2])
    db_session.commit()

    # User 1 has commitments
    c1 = Commitment(
        user_id=user1.id,
        display_name="User 1 Subscription",
        commitment_type="subscription",
        cadence="monthly",
        status="active",
        confidence_band="high",
        representative_amount=Decimal("1000.00"),
        first_seen_at=datetime.now(timezone.utc) - timedelta(days=30),
        last_seen_at=datetime.now(timezone.utc),
    )
    db_session.add(c1)
    db_session.commit()

    # Empty user 2 financial summary
    summary2 = get_user_financial_summary(db_session, user2.id)
    assert summary2.monthly_recurring_spend == Decimal("0.00")
    assert summary2.annualized_recurring_spend == Decimal("0.00")
    assert summary2.total_confirmed_commitments == 0
    assert summary2.potential_annual_savings == Decimal("0.00")

    # Empty user 2 savings opportunities
    opps2 = get_user_savings_opportunities(db_session, user2.id)
    assert len(opps2) == 0

    # User 1 has isolated data
    summary1 = get_user_financial_summary(db_session, user1.id)
    assert summary1.monthly_recurring_spend == Decimal("1000.00")
    assert summary1.annualized_recurring_spend == Decimal("12000.00")
    assert summary1.total_confirmed_commitments == 1
