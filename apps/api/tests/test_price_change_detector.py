"""Unit tests for sustained subscription price increase detector."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from app.analytics.insights.price_change_detector import detect_price_increase
from app.models.commitment import Commitment
from app.models.transaction import Transaction


def _make_txn(tx_date: date, amount: Decimal, direction="debit", status="successful") -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        transaction_date=datetime.combine(tx_date, datetime.min.time(), tzinfo=timezone.utc),
        amount=amount,
        currency="INR",
        direction=direction,
        transaction_status=status,
        raw_descriptor="TEST DESCRIPTOR",
        payment_channel="mandate",
    )


def test_sustained_price_increase_detected():
    """Verify CloudDesk Pro pattern: 5 charges at ₹799 followed by 3 charges at ₹999."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="CloudDesk Pro",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("799.00"),
    )

    dates_799 = [
        date(2026, 3, 15),
        date(2026, 4, 15),
        date(2026, 5, 15),
        date(2026, 6, 15),
        date(2026, 7, 15),
    ]
    dates_999 = [
        date(2026, 8, 15),
        date(2026, 9, 15),
        date(2026, 10, 15),
    ]

    txns = [_make_txn(d, Decimal("799.00")) for d in dates_799] + [
        _make_txn(d, Decimal("999.00")) for d in dates_999
    ]

    result = detect_price_increase(commitment, txns, notifications=[])
    assert result is not None
    assert result.previous_amount == Decimal("799.00")
    assert result.new_amount == Decimal("999.00")
    assert result.absolute_change == Decimal("200.00")
    assert round(float(result.percentage_change), 1) == 25.0
    assert result.effective_date.date() == date(2026, 8, 15)
    assert result.confidence_band in ("high", "medium")
    assert len(result.new_transactions) == 3


def test_utility_bill_fluctuations_not_flagged():
    """Verify FiberNet Broadband utility stream with natural fluctuations is protected."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="FiberNet Broadband",
        commitment_type="utility",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("1700.00"),
    )

    amounts = [
        (date(2026, 5, 10), Decimal("1420.00")),
        (date(2026, 6, 10), Decimal("1850.00")),
        (date(2026, 7, 10), Decimal("1290.00")),
        (date(2026, 8, 10), Decimal("2100.00")),
        (date(2026, 9, 10), Decimal("1630.00")),
        (date(2026, 10, 10), Decimal("1780.00")),
    ]
    txns = [_make_txn(d, amt) for d, amt in amounts]

    result = detect_price_increase(commitment, txns, notifications=[])
    assert result is None, "Utility bills with fluctuating charges should not trigger subscription price increase alerts"


def test_isolated_outlier_not_sustained_price_increase():
    """An isolated high charge does not constitute a sustained price increase regime."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="DevTools Premium",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("500.00"),
    )

    dates_and_amounts = [
        (date(2026, 4, 1), Decimal("500.00")),
        (date(2026, 5, 1), Decimal("500.00")),
        (date(2026, 6, 1), Decimal("500.00")),
        (date(2026, 7, 1), Decimal("1200.00")),  # isolated spike
        (date(2026, 8, 1), Decimal("500.00")),
        (date(2026, 9, 1), Decimal("500.00")),
    ]
    txns = [_make_txn(d, amt) for d, amt in dates_and_amounts]

    result = detect_price_increase(commitment, txns, notifications=[])
    assert result is None, "Single spike must not trigger sustained price increase"
