"""Unit tests for free trial to paid conversion detector."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from app.analytics.insights.trial_conversion_detector import detect_trial_conversion
from app.models.commitment import Commitment
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction


def _make_txn(tx_date: date, amount: Decimal, desc="SynthWrite AI") -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        transaction_date=datetime.combine(tx_date, datetime.min.time(), tzinfo=timezone.utc),
        amount=amount,
        currency="INR",
        direction="debit",
        transaction_status="successful",
        raw_descriptor=desc,
        normalised_descriptor=desc,
        payment_channel="mandate",
    )


def test_trial_to_paid_conversion_detected():
    """Verify SynthWrite AI scenario: trial_started notification followed by paid charges."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="SynthWrite AI",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("1299.00"),
    )

    notif = PaymentNotification(
        id=uuid.uuid4(),
        merchant_hint="SynthWrite AI",
        event_type="trial_started",
        event_timestamp=datetime(2026, 5, 10, 10, 0, tzinfo=timezone.utc),
        message_text="Welcome to SynthWrite AI! Your 14-day free trial has begun.",
        payment_mechanism="mandate",
    )

    zero_auth = _make_txn(date(2026, 5, 10), Decimal("0.00"))
    paid_1 = _make_txn(date(2026, 5, 24), Decimal("1299.00"))
    paid_2 = _make_txn(date(2026, 6, 24), Decimal("1299.00"))

    txns = [zero_auth, paid_1, paid_2]

    res = detect_trial_conversion(commitment, txns, [notif])
    assert res is not None
    assert res.first_paid_amount == Decimal("1299.00")
    assert res.conversion_date.date() == date(2026, 5, 24)
    assert res.confidence_band == "high"
    assert "converted" in res.explanation.lower()


def test_zero_dollar_auth_never_flagged_without_paid_conversion():
    """Trust safeguard: ₹0 authorization ping without subsequent paid debits must NEVER be flagged as paid."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="TrialApp Service",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("0.00"),
    )

    notif = PaymentNotification(
        id=uuid.uuid4(),
        merchant_hint="TrialApp",
        event_type="trial_started",
        event_timestamp=datetime(2026, 5, 1, 10, 0, tzinfo=timezone.utc),
        message_text="Free trial initiated.",
        payment_mechanism="card",
    )

    zero_auth = _make_txn(date(2026, 5, 1), Decimal("0.00"))

    res = detect_trial_conversion(commitment, [zero_auth], [notif])
    assert res is None, "A zero-dollar authorization without subsequent paid debit cannot be flagged as converted."


def test_no_trial_notifications_returns_none():
    """Standard subscription without trial notification does not trigger trial conversion."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="StreamPulse Entertainment",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("499.00"),
    )

    txns = [
        _make_txn(date(2026, 1, 1), Decimal("499.00")),
        _make_txn(date(2026, 2, 1), Decimal("499.00")),
    ]

    res = detect_trial_conversion(commitment, txns, notifications=[])
    assert res is None
