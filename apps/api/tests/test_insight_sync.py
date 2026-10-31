"""Tests for insight persistence, idempotent sync, and user review status preservation."""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.insights.insight_sync import (
    sync_post_cancellation_insight,
    sync_potentially_unused_insight,
    sync_price_increase_insight,
)
from app.analytics.insights.post_cancellation_detector import PostCancellationResult
from app.analytics.insights.price_change_detector import PriceIncreaseResult
from app.analytics.insights.usage_analyzer import UsageAnalysisResult
from app.models.account import Account
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.transaction import Transaction
from app.models.usage_coverage import UsageCoverage
from app.repositories.user_repository import UserRepository


def _make_txn(user_id: uuid.UUID, account_id: uuid.UUID, tx_date: date, amount: Decimal) -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        user_id=user_id,
        account_id=account_id,
        transaction_date=datetime.combine(tx_date, datetime.min.time(), tzinfo=timezone.utc),
        amount=amount,
        currency="INR",
        direction="debit",
        transaction_status="successful",
        raw_descriptor="TEST DESCRIPTOR",
        payment_channel="mandate",
    )


def test_insight_sync_idempotency_and_preservation(db_session: Session):
    """Verify that multiple sync executions do not create duplicate insights and preserve user status."""
    user = UserRepository.get_or_create_demo_user(db_session)

    account = Account(
        id=uuid.uuid4(),
        user_id=user.id,
        label="Primary Checking",
        account_type="savings",
        currency="INR",
    )
    db_session.add(account)
    db_session.commit()

    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=user.id,
        display_name="CloudDesk Pro",
        commitment_type="subscription",
        cadence="monthly",
        currency="INR",
        representative_amount=Decimal("799.00"),
        first_seen_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        last_seen_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        detector_version="v1.0",
        confidence_band="high",
    )
    db_session.add(commitment)
    db_session.commit()

    old_txs = [_make_txn(user.id, account.id, date(2026, 6, 15), Decimal("799.00"))]
    new_txs = [_make_txn(user.id, account.id, date(2026, 8, 15), Decimal("999.00"))]
    db_session.add_all(old_txs + new_txs)
    db_session.commit()

    result = PriceIncreaseResult(
        commitment_id=str(commitment.id),
        previous_amount=Decimal("799.00"),
        new_amount=Decimal("999.00"),
        absolute_change=Decimal("200.00"),
        percentage_change=Decimal("25.03"),
        effective_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
        confidence_score=Decimal("95.00"),
        confidence_band="high",
        explanation="Price increased from ₹799 to ₹999.",
        detector_version="v1.0",
        old_transactions=old_txs,
        new_transactions=new_txs,
    )

    # 1. First sync creates insight
    ins1 = sync_price_increase_insight(db_session, user.id, commitment, result)
    db_session.commit()
    assert ins1.status == "open"

    # Count insights in DB
    count1 = db_session.execute(
        select(CommitmentInsight).where(CommitmentInsight.user_id == user.id)
    ).scalars().all()
    assert len(count1) == 1

    # 2. User acknowledges the insight
    ins1.status = "acknowledged"
    ins1.user_action = "acknowledged"
    ins1.user_notes = "Known price hike accepted by user"
    db_session.commit()

    # 3. Second sync with same data must NOT duplicate and MUST preserve acknowledged status
    ins2 = sync_price_increase_insight(db_session, user.id, commitment, result)
    db_session.commit()

    assert ins2.id == ins1.id
    assert ins2.status == "acknowledged"
    assert ins2.user_notes == "Known price hike accepted by user"

    count2 = db_session.execute(
        select(CommitmentInsight).where(CommitmentInsight.user_id == user.id)
    ).scalars().all()
    assert len(count2) == 1, "Idempotent sync must not duplicate records"
