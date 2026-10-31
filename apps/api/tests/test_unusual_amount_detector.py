"""Unit tests for isolated unusual amount detector."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from app.analytics.insights.unusual_amount_detector import detect_unusual_amount
from app.models.commitment import Commitment
from app.models.transaction import Transaction


def _make_txn(tx_date: date, amount: Decimal) -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        transaction_date=datetime.combine(tx_date, datetime.min.time(), tzinfo=timezone.utc),
        amount=amount,
        currency="INR",
        direction="debit",
        transaction_status="successful",
        raw_descriptor="TEST SERVICE",
        payment_channel="mandate",
    )


def test_isolated_spike_detected():
    """An unexpected 3x spike in a fixed monthly subscription is flagged as unusual."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="CloudStorage Service",
        commitment_type="subscription",
        cadence="monthly",
        representative_amount=Decimal("499.00"),
    )

    txns = [
        _make_txn(date(2026, 4, 1), Decimal("499.00")),
        _make_txn(date(2026, 5, 1), Decimal("499.00")),
        _make_txn(date(2026, 6, 1), Decimal("499.00")),
        _make_txn(date(2026, 7, 1), Decimal("1499.00")),  # 3x spike
        _make_txn(date(2026, 8, 1), Decimal("499.00")),
    ]

    results = detect_unusual_amount(commitment, txns, price_change_detected=False)
    assert len(results) == 1
    res = results[0]
    assert res.unusual_amount == Decimal("1499.00")
    assert res.representative_amount == Decimal("499.00")
    assert res.confidence_band in ("high", "medium")


def test_deduplication_suppresses_alerts_when_price_change_detected():
    """If a sustained price increase was detected, suppress duplicate unusual amount alerts."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="CloudDesk Pro",
        commitment_type="subscription",
        cadence="monthly",
        representative_amount=Decimal("799.00"),
    )

    txns = [
        _make_txn(date(2026, 6, 15), Decimal("799.00")),
        _make_txn(date(2026, 7, 15), Decimal("799.00")),
        _make_txn(date(2026, 8, 15), Decimal("999.00")),
        _make_txn(date(2026, 9, 15), Decimal("999.00")),
    ]

    results = detect_unusual_amount(commitment, txns, price_change_detected=True)
    assert len(results) == 0, "Sustained price increase should suppress duplicate unusual amount alerts."
