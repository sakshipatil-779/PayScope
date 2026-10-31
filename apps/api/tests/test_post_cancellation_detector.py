"""Unit tests for charge after cancellation detector."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from app.analytics.insights.post_cancellation_detector import detect_post_cancellation_charge
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction


def _make_txn(tx_date: date, amount: Decimal, status="successful") -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        transaction_date=datetime.combine(tx_date, datetime.min.time(), tzinfo=timezone.utc),
        amount=amount,
        currency="INR",
        direction="debit",
        transaction_status=status,
        raw_descriptor="SkyVault Backup",
        payment_channel="mandate",
    )


def test_post_cancellation_charge_detected_from_event():
    """Verify SkyVault scenario: cancelled July 20, charged August 15."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="SkyVault Backup",
        commitment_type="subscription",
        cadence="monthly",
    )

    cancel_evt = CancellationEvent(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        event_timestamp=datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
        event_source="notification",
        confirmation_type="explicit_notification",
        evidence_description="Subscription cancellation confirmation processed on 20-Jul-2026.",
    )

    txns = [
        _make_txn(date(2026, 6, 15), Decimal("499.00")),
        _make_txn(date(2026, 7, 15), Decimal("499.00")),  # Before cancellation
        _make_txn(date(2026, 8, 15), Decimal("499.00")),  # After cancellation!
    ]

    res = detect_post_cancellation_charge(
        commitment,
        transactions=txns,
        cancellation_events=[cancel_evt],
        notifications=[],
    )

    assert res is not None
    assert res.post_charge_amount == Decimal("499.00")
    assert res.first_post_charge_date.date() == date(2026, 8, 15)
    assert res.confidence_band == "high"
    assert "charge" in res.explanation.lower()
    # Non-inflammatory check: no inflammatory accusations
    assert "fraud" not in res.explanation.lower()
    assert "scam" not in res.explanation.lower()


def test_charges_prior_to_cancellation_not_flagged():
    """Charges prior to cancellation are normal recurring billings."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="SkyVault Backup",
        commitment_type="subscription",
        cadence="monthly",
    )

    cancel_evt = CancellationEvent(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        event_timestamp=datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
        event_source="notification",
        confirmation_type="explicit_notification",
        evidence_description="Subscription cancellation confirmation processed on 20-Jul-2026.",
    )

    txns = [
        _make_txn(date(2026, 6, 15), Decimal("499.00")),
        _make_txn(date(2026, 7, 15), Decimal("499.00")),
    ]

    res = detect_post_cancellation_charge(
        commitment,
        transactions=txns,
        cancellation_events=[cancel_evt],
        notifications=[],
    )

    assert res is None, "No charges occurred after cancellation date."


def test_failed_attempt_after_cancellation_not_flagged_as_successful_charge():
    """A failed charge attempt after cancellation is not a successful debit."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="SkyVault Backup",
        commitment_type="subscription",
        cadence="monthly",
    )

    cancel_evt = CancellationEvent(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        event_timestamp=datetime(2026, 7, 20, 10, 0, tzinfo=timezone.utc),
        event_source="notification",
        confirmation_type="explicit_notification",
        evidence_description="Subscription cancellation confirmation processed on 20-Jul-2026.",
    )

    txns = [
        _make_txn(date(2026, 8, 15), Decimal("499.00"), status="failed"),
    ]

    res = detect_post_cancellation_charge(
        commitment,
        transactions=txns,
        cancellation_events=[cancel_evt],
        notifications=[],
    )

    assert res is None, "Failed charges should not be flagged as post-cancellation debits."
