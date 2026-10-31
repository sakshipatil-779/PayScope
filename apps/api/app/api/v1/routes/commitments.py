"""Commitment discovery, management, and user review endpoints."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.analytics.commitment_detector import CommitmentDetector
from app.analytics.commitment_sync import calculate_annualised_amount
from app.analytics.date_utils import estimate_next_expected_date
from app.analytics.schemas import (
    CommitmentDetailResponse,
    CommitmentResponse,
    CommitmentSummaryResponse,
    CommitmentTimelineResponse,
    CommitmentTransactionEvidence,
    CommitmentUpdateRequest,
    DiscoveryResultResponse,
    TimelineEvent,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction
from app.models.commitment_insight import CommitmentInsight
from app.analytics.insights.schemas import InsightResponse
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/commitments", tags=["Commitments"])


def _to_commitment_response(c: Commitment, tx_count: int = 0) -> CommitmentResponse:
    """Helper to convert Commitment model to response schema."""
    return CommitmentResponse(
        id=c.id,
        user_id=c.user_id,
        merchant_id=c.merchant_id,
        display_name=c.display_name,
        commitment_type=c.commitment_type,
        cadence=c.cadence,
        amount_pattern=c.amount_pattern,
        status=c.status,
        currency=c.currency,
        representative_amount=c.representative_amount,
        amount_min=c.amount_min,
        amount_max=c.amount_max,
        first_seen_at=c.first_seen_at,
        last_seen_at=c.last_seen_at,
        next_expected_date=c.next_expected_date,
        annualised_amount=c.annualised_amount,
        annualisation_method=c.annualisation_method,
        confidence_score=c.confidence_score,
        confidence_band=c.confidence_band,
        detection_reason_codes=c.detection_reason_codes,
        detection_explanation=c.detection_explanation,
        detector_version=c.detector_version,
        user_decision=c.user_decision,
        user_decision_at=c.user_decision_at,
        transaction_count=tx_count,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.post("/discover", response_model=DiscoveryResultResponse)
def discover_commitments(
    db: Session = Depends(get_db),
) -> DiscoveryResultResponse:
    """Run recurring cadence discovery on all imported transactions for current workspace user."""
    user = UserRepository.get_or_create_demo_user(db)
    detector = CommitmentDetector(db)
    result = detector.discover_user_commitments(user.id)

    return DiscoveryResultResponse(
        total_discovered=result.total_discovered,
        active_count=result.active_count,
        candidate_count=result.candidate_count,
        needs_review_count=result.needs_review_count,
        message=f"Discovered {result.total_discovered} recurring commitments ({result.active_count} active, {result.candidate_count} candidates, {result.needs_review_count} requiring review).",
    )


@router.get("", response_model=List[CommitmentResponse])
def list_commitments(
    cadence: Optional[str] = Query(None, description="Filter by cadence"),
    commitment_type: Optional[str] = Query(None, description="Filter by commitment type"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    confidence_band: Optional[str] = Query(None, description="Filter by confidence band"),
    amount_pattern: Optional[str] = Query(None, description="Filter by amount pattern"),
    search: Optional[str] = Query(None, description="Search display name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[CommitmentResponse]:
    """List commitments for current user with filtering, search, and pagination."""
    user = UserRepository.get_or_create_demo_user(db)

    # Subquery for transaction count
    count_subq = (
        select(
            CommitmentTransaction.commitment_id,
            func.count(CommitmentTransaction.id).label("tx_count"),
        )
        .group_by(CommitmentTransaction.commitment_id)
        .subquery()
    )

    query = (
        select(Commitment, func.coalesce(count_subq.c.tx_count, 0))
        .outerjoin(count_subq, Commitment.id == count_subq.c.commitment_id)
        .where(Commitment.user_id == user.id)
    )

    if cadence:
        query = query.where(Commitment.cadence == cadence)
    if commitment_type:
        query = query.where(Commitment.commitment_type == commitment_type)
    if status_filter:
        query = query.where(Commitment.status == status_filter)
    if confidence_band:
        query = query.where(Commitment.confidence_band == confidence_band)
    if amount_pattern:
        query = query.where(Commitment.amount_pattern == amount_pattern)
    if search:
        query = query.where(Commitment.display_name.ilike(f"%{search.strip()}%"))

    query = query.order_by(Commitment.representative_amount.desc().nullslast()).offset(skip).limit(limit)
    rows = db.execute(query).all()

    return [_to_commitment_response(c, tx_count) for c, tx_count in rows]


@router.get("/summary", response_model=CommitmentSummaryResponse)
def get_commitments_summary(
    db: Session = Depends(get_db),
) -> CommitmentSummaryResponse:
    """Aggregate statistical overview of commitments for the current workspace user."""
    user = UserRepository.get_or_create_demo_user(db)

    all_commitments = list(
        db.execute(select(Commitment).where(Commitment.user_id == user.id)).scalars().all()
    )

    total = len(all_commitments)
    active = sum(1 for c in all_commitments if c.status in ("active", "user_confirmed"))
    candidates = sum(1 for c in all_commitments if c.status == "candidate")
    review_req = sum(1 for c in all_commitments if c.status in ("review_required", "needs_review"))
    confirmed = sum(1 for c in all_commitments if c.user_decision == "confirmed" or c.status == "user_confirmed")

    # Monthly spend estimate
    monthly_spend = Decimal("0.00")
    annual_spend = Decimal("0.00")

    by_cadence: Dict[str, int] = {}
    by_type: Dict[str, int] = {}
    by_band: Dict[str, int] = {}

    for c in all_commitments:
        if c.status != "marked_not_recurring":
            # Add to spend totals
            if c.annualised_amount:
                annual_spend += c.annualised_amount
                monthly_spend += round(c.annualised_amount / Decimal("12"), 2)
            elif c.representative_amount:
                if c.cadence in ("monthly", "variable_monthly"):
                    monthly_spend += c.representative_amount
                    annual_spend += c.representative_amount * Decimal("12")

        by_cadence[c.cadence] = by_cadence.get(c.cadence, 0) + 1
        by_type[c.commitment_type] = by_type.get(c.commitment_type, 0) + 1
        by_band[c.confidence_band] = by_band.get(c.confidence_band, 0) + 1

    return CommitmentSummaryResponse(
        total_commitments=total,
        active_commitments=active,
        candidate_commitments=candidates,
        review_required_commitments=review_req,
        confirmed_commitments=confirmed,
        total_monthly_spend=monthly_spend,
        total_annualised_spend=annual_spend,
        by_cadence=by_cadence,
        by_commitment_type=by_type,
        by_confidence_band=by_band,
    )


@router.get("/{commitment_id}", response_model=CommitmentDetailResponse)
def get_commitment_detail(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CommitmentDetailResponse:
    """Get full details of a commitment including all supporting transactions."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    # Fetch supporting transactions joined with Transaction details
    ev_stmt = (
        select(CommitmentTransaction, Transaction)
        .join(Transaction, CommitmentTransaction.transaction_id == Transaction.id)
        .where(CommitmentTransaction.commitment_id == commitment.id)
        .order_by(Transaction.transaction_date.desc())
    )
    ev_rows = db.execute(ev_stmt).all()

    supporting: List[CommitmentTransactionEvidence] = [
        CommitmentTransactionEvidence(
            id=ev.id,
            transaction_id=tx.id,
            relationship_role=ev.relationship_role,
            match_confidence=ev.match_confidence,
            reason=ev.reason,
            transaction_date=tx.transaction_date,
            raw_descriptor=tx.raw_descriptor,
            normalised_descriptor=tx.normalised_descriptor,
            amount=tx.amount,
            currency=tx.currency,
            payment_channel=tx.payment_channel,
            payment_reference=tx.payment_reference,
        )
        for ev, tx in ev_rows
    ]

    base_resp = _to_commitment_response(commitment, len(supporting))
    return CommitmentDetailResponse(
        **base_resp.model_dump(),
        supporting_transactions=supporting,
    )


@router.get("/{commitment_id}/transactions", response_model=List[CommitmentTransactionEvidence])
def get_commitment_transactions(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[CommitmentTransactionEvidence]:
    """Get all supporting evidence transactions for a commitment."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    ev_stmt = (
        select(CommitmentTransaction, Transaction)
        .join(Transaction, CommitmentTransaction.transaction_id == Transaction.id)
        .where(CommitmentTransaction.commitment_id == commitment.id)
        .order_by(Transaction.transaction_date.desc())
    )
    ev_rows = db.execute(ev_stmt).all()

    return [
        CommitmentTransactionEvidence(
            id=ev.id,
            transaction_id=tx.id,
            relationship_role=ev.relationship_role,
            match_confidence=ev.match_confidence,
            reason=ev.reason,
            transaction_date=tx.transaction_date,
            raw_descriptor=tx.raw_descriptor,
            normalised_descriptor=tx.normalised_descriptor,
            amount=tx.amount,
            currency=tx.currency,
            payment_channel=tx.payment_channel,
            payment_reference=tx.payment_reference,
        )
        for ev, tx in ev_rows
    ]


@router.get("/{commitment_id}/timeline", response_model=CommitmentTimelineResponse)
def get_commitment_timeline(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CommitmentTimelineResponse:
    """Build chronological timeline of all events relating to this recurring commitment."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    events: List[TimelineEvent] = []

    # 1. Fetch transactions
    ev_stmt = (
        select(CommitmentTransaction, Transaction)
        .join(Transaction, CommitmentTransaction.transaction_id == Transaction.id)
        .where(CommitmentTransaction.commitment_id == commitment.id)
        .order_by(Transaction.transaction_date.asc())
    )
    tx_rows = db.execute(ev_stmt).all()

    for ev, tx in tx_rows:
        events.append(
            TimelineEvent(
                event_id=f"txn_{tx.id}",
                event_date=tx.transaction_date,
                event_type="transaction",
                title=f"Periodic Debit: ₹{tx.amount}",
                description=f"{tx.raw_descriptor} via {tx.payment_channel}",
                amount=tx.amount,
                currency=tx.currency,
                payment_channel=tx.payment_channel,
                payment_reference=tx.payment_reference,
                metadata={"relationship_role": ev.relationship_role, "reason": ev.reason},
            )
        )

    # 2. Fetch payment notifications matching merchant if merchant_id is present
    if commitment.merchant_id:
        notif_stmt = (
            select(PaymentNotification)
            .where(
                PaymentNotification.user_id == user.id,
                (
                    PaymentNotification.merchant_hint.ilike(f"%{commitment.display_name}%")
                    | PaymentNotification.message_text.ilike(f"%{commitment.display_name}%")
                ),
            )
            .order_by(PaymentNotification.event_timestamp.asc())
        )
        notifications = list(db.execute(notif_stmt).scalars().all())
        for n in notifications:
            events.append(
                TimelineEvent(
                    event_id=f"notif_{n.id}",
                    event_date=n.event_timestamp,
                    event_type="notification",
                    title=f"Notification: {n.event_type.replace('_', ' ').title()}",
                    description=n.message_text[:200],
                    amount=n.amount,
                    currency=n.currency,
                    payment_channel=n.payment_mechanism,
                    payment_reference=n.external_synthetic_id,
                )
            )

    # 3. User decision event if recorded
    if commitment.user_decision and commitment.user_decision_at:
        events.append(
            TimelineEvent(
                event_id=f"decision_{commitment.id}",
                event_date=commitment.user_decision_at,
                event_type="user_decision",
                title=f"User Decision: {commitment.user_decision.replace('_', ' ').title()}",
                description=f"User recorded decision '{commitment.user_decision}' for this obligation.",
            )
        )

    # Sort all events chronologically
    events.sort(key=lambda e: e.event_date)

    return CommitmentTimelineResponse(
        commitment_id=commitment.id,
        display_name=commitment.display_name,
        events=events,
    )


@router.get("/{commitment_id}/insights", response_model=List[InsightResponse])
def get_commitment_insights(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> List[InsightResponse]:
    """Get all insights and detected anomalies for a commitment."""
    from app.api.v1.routes.insights import _to_insight_response
    user = UserRepository.get_or_create_demo_user(db)

    stmt = (
        select(CommitmentInsight)
        .where(
            CommitmentInsight.commitment_id == commitment_id,
            CommitmentInsight.user_id == user.id,
        )
        .options(
            joinedload(CommitmentInsight.commitment).joinedload(Commitment.merchant),
            joinedload(CommitmentInsight.evidence_items),
        )
        .order_by(CommitmentInsight.detected_at.desc())
    )
    insights = db.execute(stmt).unique().scalars().all()
    return [_to_insight_response(i) for i in insights]


@router.post("/{commitment_id}/confirm", response_model=CommitmentResponse)
def confirm_commitment(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CommitmentResponse:
    """User confirms this obligation as an active recurring commitment."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    now = datetime.now(timezone.utc)
    commitment.user_decision = "confirmed"
    commitment.user_decision_at = now
    commitment.status = "user_confirmed"
    commitment.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=user.id,
        entity_type="commitment",
        entity_id=commitment.id,
        action="confirm",
        actor_type="user",
        after_summary={
            "commitment_id": str(commitment.id),
            "display_name": commitment.display_name,
            "status": "user_confirmed",
        },
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(commitment)

    return _to_commitment_response(commitment)


@router.patch("/{commitment_id}", response_model=CommitmentResponse)
def update_commitment(
    commitment_id: uuid.UUID,
    update_data: CommitmentUpdateRequest,
    db: Session = Depends(get_db),
) -> CommitmentResponse:
    """User corrects commitment attributes (type, cadence, display name)."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    now = datetime.now(timezone.utc)
    changes: Dict[str, Any] = {}

    if update_data.display_name is not None and update_data.display_name.strip():
        changes["display_name"] = (commitment.display_name, update_data.display_name.strip())
        commitment.display_name = update_data.display_name.strip()

    if update_data.commitment_type is not None:
        valid_types = {"subscription", "membership", "utility", "insurance", "loan_emi", "other", "needs_review"}
        val = update_data.commitment_type.lower().strip()
        if val not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid commitment_type '{val}'. Must be one of {sorted(valid_types)}.",
            )
        changes["commitment_type"] = (commitment.commitment_type, val)
        commitment.commitment_type = val

    if update_data.cadence is not None:
        valid_cadences = {"weekly", "fortnightly", "monthly", "quarterly", "annual", "variable_monthly", "irregular", "unknown"}
        val = update_data.cadence.lower().strip()
        if val not in valid_cadences:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid cadence '{val}'. Must be one of {sorted(valid_cadences)}.",
            )
        changes["cadence"] = (commitment.cadence, val)
        commitment.cadence = val

        # Recalculate annualised amount and next date
        ann_amt, ann_method = calculate_annualised_amount(
            commitment.representative_amount,
            commitment.cadence,
        )
        commitment.annualised_amount = ann_amt
        commitment.annualisation_method = ann_method

        last_d = commitment.last_seen_at.date() if isinstance(commitment.last_seen_at, datetime) else commitment.last_seen_at
        commitment.next_expected_date = estimate_next_expected_date(last_d, commitment.cadence)

    commitment.user_decision = "corrected"
    commitment.user_decision_at = now
    commitment.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=user.id,
        entity_type="commitment",
        entity_id=commitment.id,
        action="update",
        actor_type="user",
        after_summary={
            "commitment_id": str(commitment.id),
            "changes": {k: [str(v[0]), str(v[1])] for k, v in changes.items()},
        },
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(commitment)

    return _to_commitment_response(commitment)


@router.post("/{commitment_id}/mark-not-recurring", response_model=CommitmentResponse)
def mark_commitment_not_recurring(
    commitment_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CommitmentResponse:
    """User marks candidate or active obligation as NOT recurring."""
    user = UserRepository.get_or_create_demo_user(db)

    commitment = db.execute(
        select(Commitment)
        .where(Commitment.id == commitment_id, Commitment.user_id == user.id)
    ).scalars().first()

    if not commitment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment with ID '{commitment_id}' not found.",
        )

    now = datetime.now(timezone.utc)
    commitment.user_decision = "not_recurring"
    commitment.user_decision_at = now
    commitment.status = "marked_not_recurring"
    commitment.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=user.id,
        entity_type="commitment",
        entity_id=commitment.id,
        action="mark_not_recurring",
        actor_type="user",
        after_summary={
            "commitment_id": str(commitment.id),
            "display_name": commitment.display_name,
            "status": "marked_not_recurring",
        },
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(commitment)

    return _to_commitment_response(commitment)
