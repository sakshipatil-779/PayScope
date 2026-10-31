"""Orchestrator for recurring commitment anomaly, price increase, trial, and usage detection."""
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.analytics.insights.config import INSIGHT_DETECTOR_VERSION
from app.analytics.insights.insight_sync import (
    sync_post_cancellation_insight,
    sync_potentially_unused_insight,
    sync_price_increase_insight,
    sync_trial_conversion_insight,
    sync_unusual_amount_insight,
)
from app.analytics.insights.post_cancellation_detector import detect_post_cancellation
from app.analytics.insights.price_change_detector import detect_price_increases
from app.analytics.insights.schemas import InsightDetectionSummary, InsightResponse
from app.analytics.insights.trial_conversion_detector import detect_trial_conversion
from app.analytics.insights.unusual_amount_detector import detect_unusual_amount
from app.analytics.insights.usage_analyzer import UsageAnalysisStatus, analyze_usage
from app.generators.phase6_fixtures import seed_phase6_supporting_data
from app.models.audit_event import AuditEvent
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.commitment_transaction import CommitmentTransaction
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction
from app.models.usage_coverage import UsageCoverage
from app.models.usage_event import UsageEvent


def run_insight_detection(db: Session, user_id: uuid.UUID) -> InsightDetectionSummary:
    """Execute all anomaly, price-change, trial, and usage detectors across user commitments."""
    start_time = time.perf_counter()

    # Ensure supporting Phase 6 data (usage coverage, cancellation records) exists for demo scenarios
    seed_phase6_supporting_data(db, user_id)

    # 1. Fetch commitments for user with transactions
    stmt = (
        select(Commitment)
        .where(Commitment.user_id == user_id)
        .options(
            joinedload(Commitment.commitment_transactions).joinedload(CommitmentTransaction.transaction),
            joinedload(Commitment.merchant),
        )
    )
    commitments = db.execute(stmt).unique().scalars().all()

    # 2. Fetch context items (notifications, coverage records, usage events, cancellation events)
    notif_stmt = select(PaymentNotification).where(PaymentNotification.user_id == user_id)
    notifications = list(db.execute(notif_stmt).scalars().all())

    cov_stmt = select(UsageCoverage).where(UsageCoverage.user_id == user_id)
    coverage_records = list(db.execute(cov_stmt).scalars().all())

    usage_stmt = select(UsageEvent).where(UsageEvent.user_id == user_id)
    usage_events = list(db.execute(usage_stmt).scalars().all())

    cancel_stmt = select(CancellationEvent).where(CancellationEvent.user_id == user_id)
    cancellation_events = list(db.execute(cancel_stmt).scalars().all())

    newly_created_insights: List[CommitmentInsight] = []
    price_increase_cnt = 0
    trial_conversion_cnt = 0
    unused_cnt = 0
    post_cancellation_cnt = 0
    unusual_amount_cnt = 0

    # 3. Analyze each commitment
    for commitment in commitments:
        # Extract and sort transactions
        txns: List[Transaction] = [
            ct.transaction for ct in commitment.commitment_transactions if ct.transaction is not None
        ]
        txns.sort(key=lambda t: t.transaction_date)

        if not txns:
            continue

        price_change_found = False

        # A. Detect sustained price increase
        price_result = detect_price_increases(commitment, txns, notifications)
        if price_result:
            price_change_found = True
            ins = sync_price_increase_insight(db, user_id, commitment, price_result)
            newly_created_insights.append(ins)
            price_increase_cnt += 1

        # B. Detect trial to paid conversion
        trial_result = detect_trial_conversion(commitment, txns, notifications)
        if trial_result:
            ins = sync_trial_conversion_insight(db, user_id, commitment, trial_result)
            newly_created_insights.append(ins)
            trial_conversion_cnt += 1

        # C. Analyze usage patterns
        usage_result = analyze_usage(commitment, txns, coverage_records, usage_events)
        if usage_result.status == UsageAnalysisStatus.POTENTIALLY_UNUSED:
            ins = sync_potentially_unused_insight(db, user_id, commitment, usage_result)
            newly_created_insights.append(ins)
            unused_cnt += 1

        # D. Detect charges after cancellation
        post_cancel_result = detect_post_cancellation(commitment, txns, cancellation_events, notifications)
        if post_cancel_result:
            ins = sync_post_cancellation_insight(db, user_id, commitment, post_cancel_result)
            newly_created_insights.append(ins)
            post_cancellation_cnt += 1

        # E. Detect isolated unusual amounts (suppressing duplicates if sustained price change was identified)
        unusual_results = detect_unusual_amount(commitment, txns, price_change_detected=price_change_found)
        for u_res in unusual_results:
            ins = sync_unusual_amount_insight(db, user_id, commitment, u_res)
            newly_created_insights.append(ins)
            unusual_amount_cnt += 1

    db.commit()

    # 4. Record Audit Event
    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=user_id,
        entity_type="insight_detection",
        entity_id=user_id,
        action="detection_executed",
        actor_type="system",
        after_summary={
            "detector_version": INSIGHT_DETECTOR_VERSION,
            "commitments_evaluated": len(commitments),
            "price_increases": price_increase_cnt,
            "trial_conversions": trial_conversion_cnt,
            "potentially_unused": unused_cnt,
            "post_cancellation_charges": post_cancellation_cnt,
            "unusual_amounts": unusual_amount_cnt,
        },
        created_at=datetime.now(timezone.utc),
    )
    db.add(audit)
    db.commit()

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # 5. Query all active insights for response
    all_insights_stmt = (
        select(CommitmentInsight)
        .where(CommitmentInsight.user_id == user_id)
        .options(
            joinedload(CommitmentInsight.commitment).joinedload(Commitment.merchant),
            joinedload(CommitmentInsight.evidence_items),
        )
        .order_by(CommitmentInsight.detected_at.desc())
    )
    all_insights = db.execute(all_insights_stmt).unique().scalars().all()

    insight_responses = []
    for ins in all_insights:
        commitment_name = ins.commitment.display_name if ins.commitment else "Unknown Commitment"
        merchant_name = ins.commitment.merchant.canonical_name if (ins.commitment and ins.commitment.merchant) else None
        insight_responses.append(
            InsightResponse(
                id=ins.id,
                user_id=ins.user_id,
                commitment_id=ins.commitment_id,
                commitment_name=commitment_name,
                merchant_name=merchant_name,
                insight_type=ins.insight_type,
                severity=ins.severity,
                status=ins.status,
                title=ins.title,
                summary=ins.summary,
                explanation=ins.explanation,
                confidence_score=ins.confidence_score,
                confidence_band=ins.confidence_band,
                detected_at=ins.detected_at,
                detector_version=ins.detector_version,
                user_action=ins.status if ins.status != "open" else None,
                user_action_at=ins.resolved_at or ins.acknowledged_at,
                user_notes=None,
                evidence_count=len(ins.evidence_items),
                created_at=ins.created_at,
                updated_at=ins.updated_at,
            )
        )

    return InsightDetectionSummary(
        status="completed",
        total_detected=len(all_insights),
        price_increases_detected=price_increase_cnt,
        trial_conversions_detected=trial_conversion_cnt,
        potentially_unused_detected=unused_cnt,
        post_cancellation_charges_detected=post_cancellation_cnt,
        unusual_amounts_detected=unusual_amount_cnt,
        duration_ms=duration_ms,
        insights=insight_responses,
    )
