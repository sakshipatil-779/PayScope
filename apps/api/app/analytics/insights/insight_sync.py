"""Database synchronization and idempotent persistence layer for commitment insights."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.insights.evidence_linker import (
    create_cancellation_evidence,
    create_coverage_evidence,
    create_notification_evidence,
    create_transaction_evidence,
)
from app.analytics.insights.post_cancellation_detector import PostCancellationResult
from app.analytics.insights.price_change_detector import PriceIncreaseResult
from app.analytics.insights.trial_conversion_detector import TrialConversionResult
from app.analytics.insights.unusual_amount_detector import UnusualAmountResult
from app.analytics.insights.usage_analyzer import UsageAnalysisResult
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.insight_evidence import InsightEvidence
from app.models.price_event import PriceEvent


def sync_price_increase_insight(
    db: Session,
    user_id: uuid.UUID,
    commitment: Commitment,
    result: PriceIncreaseResult,
) -> CommitmentInsight:
    """Idempotently persist a sustained price increase insight and structured price event."""
    now = datetime.now(timezone.utc)
    fingerprint = f"price_increase_{commitment.id}_{result.effective_date.date()}_{result.new_amount}"

    # 1. Check if insight already exists
    stmt = select(CommitmentInsight).where(CommitmentInsight.unique_fingerprint == fingerprint)
    existing: Optional[CommitmentInsight] = db.execute(stmt).scalars().first()

    if existing:
        # Preserve user review status (acknowledged, resolved, dismissed)
        existing.explanation = result.explanation
        existing.confidence_score = result.confidence_score
        existing.confidence_band = result.confidence_band
        existing.updated_at = now
        return existing

    # 2. Create structured price_events record
    price_evt = PriceEvent(
        id=uuid.uuid4(),
        commitment_id=commitment.id,
        event_type="amount_increase",
        previous_amount=result.previous_amount,
        new_amount=result.new_amount,
        currency=commitment.currency,
        absolute_change=result.absolute_change,
        percentage_change=result.percentage_change,
        effective_or_detected_at=result.effective_date,
        confidence_band=result.confidence_band,
        explanation=result.explanation,
        detector_version=result.detector_version,
        created_at=now,
    )
    db.add(price_evt)

    # 3. Create CommitmentInsight
    insight = CommitmentInsight(
        id=uuid.uuid4(),
        user_id=user_id,
        commitment_id=commitment.id,
        insight_type="price_increase",
        severity="medium",
        status="open",
        title=f"Price Increase: {commitment.display_name} (+₹{result.absolute_change})",
        summary=f"Billing increased from ₹{result.previous_amount} to ₹{result.new_amount} (+{result.percentage_change:.1f}%).",
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        confidence_band=result.confidence_band,
        detected_at=result.effective_date,
        detector_version=result.detector_version,
        unique_fingerprint=fingerprint,
        created_at=now,
        updated_at=now,
    )
    db.add(insight)
    db.flush()

    # 4. Link evidence
    for t in result.old_transactions:
        db.add(create_transaction_evidence(insight.id, t, "previous_price_evidence"))
    for t in result.new_transactions:
        db.add(create_transaction_evidence(insight.id, t, "new_price_evidence"))
    if result.matching_notification:
        db.add(create_notification_evidence(insight.id, result.matching_notification, "price_notification"))

    return insight


def sync_trial_conversion_insight(
    db: Session,
    user_id: uuid.UUID,
    commitment: Commitment,
    result: TrialConversionResult,
) -> CommitmentInsight:
    """Idempotently persist a trial to paid conversion insight."""
    now = datetime.now(timezone.utc)
    fingerprint = f"trial_conversion_{commitment.id}_{result.conversion_date.date()}_{result.first_paid_amount}"

    stmt = select(CommitmentInsight).where(CommitmentInsight.unique_fingerprint == fingerprint)
    existing: Optional[CommitmentInsight] = db.execute(stmt).scalars().first()

    if existing:
        existing.explanation = result.explanation
        existing.updated_at = now
        return existing

    insight = CommitmentInsight(
        id=uuid.uuid4(),
        user_id=user_id,
        commitment_id=commitment.id,
        insight_type="trial_conversion",
        severity="low",
        status="open",
        title=f"Trial Converted to Paid: {commitment.display_name}",
        summary=f"Free trial converted into recurring paid billing of ₹{result.first_paid_amount}.",
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        confidence_band=result.confidence_band,
        detected_at=result.conversion_date,
        detector_version=result.detector_version,
        unique_fingerprint=fingerprint,
        created_at=now,
        updated_at=now,
    )
    db.add(insight)
    db.flush()

    if result.trial_notification:
        db.add(create_notification_evidence(insight.id, result.trial_notification, "trial_start_evidence"))
    if result.converted_transaction:
        db.add(create_transaction_evidence(insight.id, result.converted_transaction, "paid_conversion_evidence"))
    for t in result.subsequent_transactions[:2]:
        db.add(create_transaction_evidence(insight.id, t, "subsequent_paid_debit"))

    return insight


def sync_potentially_unused_insight(
    db: Session,
    user_id: uuid.UUID,
    commitment: Commitment,
    result: UsageAnalysisResult,
) -> CommitmentInsight:
    """Idempotently persist a potentially unused commitment insight."""
    now = datetime.now(timezone.utc)
    fingerprint = f"potentially_unused_{commitment.id}_{result.coverage_start}_{result.coverage_end}"

    stmt = select(CommitmentInsight).where(CommitmentInsight.unique_fingerprint == fingerprint)
    existing: Optional[CommitmentInsight] = db.execute(stmt).scalars().first()

    if existing:
        existing.explanation = result.explanation
        existing.updated_at = now
        return existing

    insight = CommitmentInsight(
        id=uuid.uuid4(),
        user_id=user_id,
        commitment_id=commitment.id,
        insight_type="potentially_unused",
        severity="medium",
        status="open",
        title=f"Potentially Unused: {commitment.display_name}",
        summary=f"No usage recorded during {result.coverage_days} days of complete activity tracking.",
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        confidence_band=result.confidence_band,
        detected_at=now,
        detector_version=result.detector_version,
        unique_fingerprint=fingerprint,
        created_at=now,
        updated_at=now,
    )
    db.add(insight)
    db.flush()

    if result.coverage_record:
        db.add(create_coverage_evidence(insight.id, result.coverage_record, "usage_coverage_evidence"))

    return insight


def sync_post_cancellation_insight(
    db: Session,
    user_id: uuid.UUID,
    commitment: Commitment,
    result: PostCancellationResult,
) -> CommitmentInsight:
    """Idempotently persist a post-cancellation debit insight."""
    now = datetime.now(timezone.utc)
    first_tx_id = result.post_transactions[0].id if result.post_transactions else uuid.uuid4()
    fingerprint = f"post_cancellation_{commitment.id}_{result.first_post_charge_date.date()}_{first_tx_id}"

    stmt = select(CommitmentInsight).where(CommitmentInsight.unique_fingerprint == fingerprint)
    existing: Optional[CommitmentInsight] = db.execute(stmt).scalars().first()

    if existing:
        existing.explanation = result.explanation
        existing.updated_at = now
        return existing

    insight = CommitmentInsight(
        id=uuid.uuid4(),
        user_id=user_id,
        commitment_id=commitment.id,
        insight_type="post_cancellation_charge",
        severity="high",
        status="open",
        title=f"Charge After Cancellation: {commitment.display_name} (₹{result.post_charge_amount})",
        summary=f"Successful charge of ₹{result.post_charge_amount} observed on {result.first_post_charge_date.strftime('%d-%b-%Y')} after cancellation.",
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        confidence_band=result.confidence_band,
        detected_at=result.first_post_charge_date,
        detector_version=result.detector_version,
        unique_fingerprint=fingerprint,
        created_at=now,
        updated_at=now,
    )
    db.add(insight)
    db.flush()

    # Link evidence
    if result.cancellation_event:
        db.add(create_cancellation_evidence(insight.id, result.cancellation_event, "cancellation_evidence"))
    elif result.cancellation_notification:
        db.add(create_notification_evidence(insight.id, result.cancellation_notification, "cancellation_evidence"))

    for t in result.post_transactions:
        db.add(create_transaction_evidence(insight.id, t, "post_cancellation_debit"))

    return insight


def sync_unusual_amount_insight(
    db: Session,
    user_id: uuid.UUID,
    commitment: Commitment,
    result: UnusualAmountResult,
) -> CommitmentInsight:
    """Idempotently persist an isolated unusual amount insight."""
    now = datetime.now(timezone.utc)
    fingerprint = f"unusual_amount_{commitment.id}_{result.unusual_transaction.id}"

    stmt = select(CommitmentInsight).where(CommitmentInsight.unique_fingerprint == fingerprint)
    existing: Optional[CommitmentInsight] = db.execute(stmt).scalars().first()

    if existing:
        existing.explanation = result.explanation
        existing.updated_at = now
        return existing

    insight = CommitmentInsight(
        id=uuid.uuid4(),
        user_id=user_id,
        commitment_id=commitment.id,
        insight_type="unusual_amount",
        severity="medium",
        status="open",
        title=f"Unusual Charge Amount: {commitment.display_name} (₹{result.unusual_amount})",
        summary=f"Charge of ₹{result.unusual_amount} deviates by +{result.percentage_deviation:.1f}% from representative ₹{result.representative_amount}.",
        explanation=result.explanation,
        confidence_score=result.confidence_score,
        confidence_band=result.confidence_band,
        detected_at=result.transaction_date,
        detector_version=result.detector_version,
        unique_fingerprint=fingerprint,
        created_at=now,
        updated_at=now,
    )
    db.add(insight)
    db.flush()

    db.add(create_transaction_evidence(insight.id, result.unusual_transaction, "unusual_amount_evidence"))
    for t in result.baseline_transactions:
        db.add(create_transaction_evidence(insight.id, t, "baseline_evidence"))

    return insight

