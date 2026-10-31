"""Unit tests for confidence calculation."""
from decimal import Decimal
from app.analytics.amount_analyzer import AmountAnalysis
from app.analytics.cadence_classifier import CadenceClassification
from app.analytics.confidence import calculate_confidence
from app.analytics.interval_analyzer import IntervalAnalysis


def test_confidence_high_monthly():
    cadence_res = CadenceClassification(
        cadence="monthly",
        is_recurring=True,
        is_candidate_only=False,
        primary_reason="Regular monthly",
    )
    interval_info = IntervalAnalysis(
        count=6,
        median_interval=30.5,
        std_dev_interval=0.5,
    )
    amount_info = AmountAnalysis(
        count=6,
        representative_amount=Decimal("499.00"),
        amount_min=Decimal("499.00"),
        amount_max=Decimal("499.00"),
        amount_pattern="fixed",
    )

    assessment = calculate_confidence(
        cadence_res=cadence_res,
        interval_info=interval_info,
        amount_info=amount_info,
        merchant_match_confidence="high",
        is_merchant_resolved=True,
        payment_channels={"upi_autopay"},
        display_name="StreamPulse Entertainment",
    )

    assert assessment.score >= Decimal("80.00")
    assert assessment.band == "high"
    assert "SUFFICIENT_TRANSACTION_HISTORY" in assessment.reason_codes
    assert "FIXED_AMOUNT_OBSERVED" in assessment.reason_codes
    assert "StreamPulse Entertainment" in assessment.explanation


def test_confidence_candidate_annual():
    cadence_res = CadenceClassification(
        cadence="annual",
        is_recurring=False,
        is_candidate_only=True,
        primary_reason="Single annual observation",
    )
    interval_info = IntervalAnalysis(count=1)
    amount_info = AmountAnalysis(
        count=1,
        representative_amount=Decimal("14500.00"),
        amount_min=Decimal("14500.00"),
        amount_max=Decimal("14500.00"),
        amount_pattern="insufficient_data",
    )

    assessment = calculate_confidence(
        cadence_res=cadence_res,
        interval_info=interval_info,
        amount_info=amount_info,
        merchant_match_confidence="high",
        is_merchant_resolved=True,
        display_name="Suraksha General Insurance",
    )

    assert assessment.band == "low"
    assert "SINGLE_ANNUAL_OBSERVATION_REQUIRES_MORE_EVIDENCE" in assessment.reason_codes


def test_confidence_unresolved_merchant():
    cadence_res = CadenceClassification(
        cadence="monthly",
        is_recurring=True,
        is_candidate_only=False,
        primary_reason="Regular monthly",
    )
    interval_info = IntervalAnalysis(count=6, median_interval=30.0, std_dev_interval=0.0)
    amount_info = AmountAnalysis(
        count=6,
        representative_amount=Decimal("850.00"),
        amount_min=Decimal("850.00"),
        amount_max=Decimal("850.00"),
        amount_pattern="fixed",
    )

    assessment = calculate_confidence(
        cadence_res=cadence_res,
        interval_info=interval_info,
        amount_info=amount_info,
        merchant_match_confidence=None,
        is_merchant_resolved=False,
        display_name="RAZORPAY*UNKNOWN_MEMBER",
    )

    assert assessment.band == "needs_review"
    assert "UNRESOLVED_MERCHANT_DESCRIPTOR" in assessment.reason_codes
