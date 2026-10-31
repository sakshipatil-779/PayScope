"""API routes for Commitment Anomaly, Price Increase, Trial Conversion, and Usage Insights."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload
from app.analytics.insights import (
    EvidenceItemResponse,
    InsightAcknowledgeRequest,
    InsightDetailResponse,
    InsightDetectionSummary,
    InsightDismissRequest,
    InsightResolveRequest,
    InsightResponse,
    InsightSummaryResponse,
    PriceEventResponse,
    run_insight_detection,
)
from app.db.session import get_db
from app.models.audit_event import AuditEvent
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.insight_evidence import InsightEvidence
from app.models.price_event import PriceEvent
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/insights", tags=["Commitment Insights"])


def _to_evidence_response(e: InsightEvidence) -> EvidenceItemResponse:
    ev_type = "other"
    summary = e.evidence_role.replace("_", " ").title()
    ts = e.created_at

    if e.transaction:
        ev_type = "transaction"
        ts = e.transaction.transaction_date
        summary = f"Transaction: ₹{e.transaction.amount} ({e.transaction.raw_descriptor}) on {ts.strftime('%d-%b-%Y')}"
    elif e.notification:
        ev_type = "notification"
        ts = e.notification.event_timestamp
        summary = f"Notification: {e.notification.event_type} on {ts.strftime('%d-%b-%Y')} - {e.notification.message_text[:80]}"
    elif e.usage_coverage:
        ev_type = "usage_coverage"
        summary = f"Activity Tracking: {e.usage_coverage.source_label} ({e.usage_coverage.coverage_start} to {e.usage_coverage.coverage_end})"
    elif e.cancellation_event:
        ev_type = "cancellation_event"
        ts = e.cancellation_event.event_timestamp
        summary = f"Cancellation Confirmation on {ts.strftime('%d-%b-%Y')}: {e.cancellation_event.evidence_description}"
    elif e.usage_event:
        ev_type = "usage_event"
        ts = e.usage_event.event_at
        summary = f"Usage Event: {e.usage_event.event_type} on {ts.strftime('%d-%b-%Y')}"

    return EvidenceItemResponse(
        id=e.id,
        insight_id=e.insight_id,
        evidence_type=ev_type,
        role=e.evidence_role,
        summary=summary,
        timestamp=ts,
        transaction_id=e.transaction_id,
        notification_id=e.notification_id,
        usage_coverage_id=e.usage_coverage_id,
        usage_event_id=e.usage_event_id,
        cancellation_event_id=e.cancellation_event_id,
        created_at=e.created_at,
    )


def _to_insight_response(ins: CommitmentInsight) -> InsightResponse:
    commitment_name = ins.commitment.display_name if ins.commitment else "Unknown Commitment"
    merchant_name = ins.commitment.merchant.canonical_name if (ins.commitment and ins.commitment.merchant) else None
    return InsightResponse(
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
        evidence_count=len(ins.evidence_items) if ins.evidence_items else 0,
        created_at=ins.created_at,
        updated_at=ins.updated_at,
    )


@router.post("/detect", response_model=InsightDetectionSummary, status_code=status.HTTP_200_OK)
def detect_insights(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional user ID; defaults to demo user"),
    db: Session = Depends(get_db),
):
    """Execute all anomaly, price-change, trial, and usage detectors across user commitments."""
    target_user_id = user_id or UserRepository.get_or_create_demo_user(db).id
    return run_insight_detection(db, target_user_id)


@router.get("/summary", response_model=InsightSummaryResponse, status_code=status.HTTP_200_OK)
def get_insights_summary(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Return aggregated metric counts and estimated monthly impact across all open insights."""
    target_user_id = user_id or UserRepository.get_or_create_demo_user(db).id

    stmt = (
        select(CommitmentInsight)
        .where(
            CommitmentInsight.user_id == target_user_id,
            CommitmentInsight.status == "open",
        )
        .options(
            joinedload(CommitmentInsight.commitment),
        )
    )
    open_insights = list(db.execute(stmt).scalars().all())

    price_increases = sum(1 for i in open_insights if i.insight_type == "price_increase")
    trial_conversions = sum(1 for i in open_insights if i.insight_type == "trial_conversion")
    potentially_unused = sum(1 for i in open_insights if i.insight_type == "potentially_unused")
    post_cancellation = sum(1 for i in open_insights if i.insight_type == "post_cancellation_charge")
    unusual_amounts = sum(1 for i in open_insights if i.insight_type == "unusual_amount")

    high_sev = sum(1 for i in open_insights if i.severity == "high")
    med_sev = sum(1 for i in open_insights if i.severity == "medium")
    low_sev = sum(1 for i in open_insights if i.severity == "low")

    # Calculate estimated monthly impact
    monthly_impact = Decimal("0.00")
    for ins in open_insights:
        if ins.insight_type == "price_increase" and ins.commitment_id:
            # Look up price event delta
            pe = db.execute(
                select(PriceEvent).where(PriceEvent.commitment_id == ins.commitment_id)
            ).scalars().first()
            if pe and pe.absolute_change:
                monthly_impact += pe.absolute_change
        elif ins.insight_type in ("potentially_unused", "post_cancellation_charge"):
            if ins.commitment and ins.commitment.representative_amount:
                monthly_impact += ins.commitment.representative_amount

    return InsightSummaryResponse(
        total_open=len(open_insights),
        price_increases=price_increases,
        trial_conversions=trial_conversions,
        potentially_unused=potentially_unused,
        post_cancellation_charges=post_cancellation,
        unusual_amounts=unusual_amounts,
        high_severity=high_sev,
        medium_severity=med_sev,
        low_severity=low_sev,
        estimated_monthly_impact=monthly_impact,
    )


def _query_insights(
    db: Session,
    user_id: Optional[uuid.UUID] = None,
    insight_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    commitment_id: Optional[uuid.UUID] = None,
    merchant_id: Optional[uuid.UUID] = None,
    confidence_band: Optional[str] = None,
) -> List[InsightResponse]:
    target_user_id = user_id or UserRepository.get_or_create_demo_user(db).id

    stmt = (
        select(CommitmentInsight)
        .where(CommitmentInsight.user_id == target_user_id)
        .options(
            joinedload(CommitmentInsight.commitment).joinedload(Commitment.merchant),
            joinedload(CommitmentInsight.evidence_items),
        )
        .order_by(CommitmentInsight.detected_at.desc())
    )

    if insight_type:
        stmt = stmt.where(CommitmentInsight.insight_type == insight_type)
    if severity:
        stmt = stmt.where(CommitmentInsight.severity == severity)
    if status:
        stmt = stmt.where(CommitmentInsight.status == status)
    if commitment_id:
        stmt = stmt.where(CommitmentInsight.commitment_id == commitment_id)
    if confidence_band:
        stmt = stmt.where(CommitmentInsight.confidence_band == confidence_band)
    if merchant_id:
        stmt = stmt.join(Commitment).where(Commitment.merchant_id == merchant_id)

    insights = db.execute(stmt).unique().scalars().all()
    return [_to_insight_response(i) for i in insights]


@router.get("/price-changes", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_price_change_insights(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all price increase insights."""
    return _query_insights(db, user_id=user_id, insight_type="price_increase")


@router.get("/trial-conversions", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_trial_conversion_insights(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all free trial to paid conversion insights."""
    return _query_insights(db, user_id=user_id, insight_type="trial_conversion")


@router.get("/unused", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_unused_insights(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all potentially unused commitment insights."""
    return _query_insights(db, user_id=user_id, insight_type="potentially_unused")


@router.get("/post-cancellation", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_post_cancellation_insights(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all charges occurring after cancellation insights."""
    return _query_insights(db, user_id=user_id, insight_type="post_cancellation_charge")


@router.get("/unusual-amounts", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_unusual_amount_insights(
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve all isolated unusual charge amount insights."""
    return _query_insights(db, user_id=user_id, insight_type="unusual_amount")


@router.get("/", response_model=List[InsightResponse], status_code=status.HTTP_200_OK)
def get_insights(
    insight_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    commitment_id: Optional[uuid.UUID] = Query(None),
    merchant_id: Optional[uuid.UUID] = Query(None),
    confidence_band: Optional[str] = Query(None),
    user_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
):
    """Query commitment insights with multidimensional filters."""
    return _query_insights(
        db,
        user_id=user_id,
        insight_type=insight_type,
        severity=severity,
        status=status,
        commitment_id=commitment_id,
        merchant_id=merchant_id,
        confidence_band=confidence_band,
    )


@router.get("/{insight_id}", response_model=InsightDetailResponse, status_code=status.HTTP_200_OK)
def get_insight_detail(
    insight_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve full deep-dive details for an insight, including supporting evidence items."""
    stmt = (
        select(CommitmentInsight)
        .where(CommitmentInsight.id == insight_id)
        .options(
            joinedload(CommitmentInsight.commitment).joinedload(Commitment.merchant),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.transaction),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.notification),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.usage_coverage),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.cancellation_event),
            joinedload(CommitmentInsight.evidence_items).joinedload(InsightEvidence.usage_event),
        )
    )
    ins = db.execute(stmt).unique().scalars().first()
    if not ins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commitment insight {insight_id} not found.",
        )

    # Fetch price event if available
    pe_stmt = select(PriceEvent).where(PriceEvent.commitment_id == ins.commitment_id).order_by(PriceEvent.created_at.desc())
    pe = db.execute(pe_stmt).scalars().first()
    pe_resp = PriceEventResponse.model_validate(pe) if pe else None

    # Format evidence items
    evidence_resps = [
        _to_evidence_response(e)
        for e in sorted(ins.evidence_items, key=lambda x: x.created_at)
    ]

    base = _to_insight_response(ins)
    return InsightDetailResponse(
        **base.model_dump(),
        commitment_representative_amount=ins.commitment.representative_amount if ins.commitment else None,
        commitment_cadence=ins.commitment.cadence if ins.commitment else None,
        price_event=pe_resp,
        evidence_items=evidence_resps,
    )


@router.post("/{insight_id}/acknowledge", response_model=InsightResponse, status_code=status.HTTP_200_OK)
def acknowledge_insight(
    insight_id: uuid.UUID,
    payload: InsightAcknowledgeRequest,
    db: Session = Depends(get_db),
):
    """Mark an insight as acknowledged by the user."""
    ins = db.execute(select(CommitmentInsight).where(CommitmentInsight.id == insight_id)).scalars().first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    now = datetime.now(timezone.utc)
    ins.status = "acknowledged"
    ins.acknowledged_at = now
    ins.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=ins.user_id,
        entity_type="commitment_insight",
        entity_id=ins.id,
        action="acknowledge",
        actor_type="user",
        after_summary={"status": ins.status, "notes": payload.notes},
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(ins)

    return _to_insight_response(ins)


@router.post("/{insight_id}/dismiss", response_model=InsightResponse, status_code=status.HTTP_200_OK)
def dismiss_insight(
    insight_id: uuid.UUID,
    payload: InsightDismissRequest,
    db: Session = Depends(get_db),
):
    """Mark an insight as dismissed by the user."""
    ins = db.execute(select(CommitmentInsight).where(CommitmentInsight.id == insight_id)).scalars().first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    now = datetime.now(timezone.utc)
    ins.status = "dismissed"
    ins.resolved_at = now
    ins.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=ins.user_id,
        entity_type="commitment_insight",
        entity_id=ins.id,
        action="dismiss",
        actor_type="user",
        after_summary={"status": ins.status, "reason": payload.reason, "notes": payload.notes},
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(ins)

    return _to_insight_response(ins)


@router.post("/{insight_id}/resolve", response_model=InsightResponse, status_code=status.HTTP_200_OK)
def resolve_insight(
    insight_id: uuid.UUID,
    payload: InsightResolveRequest,
    db: Session = Depends(get_db),
):
    """Mark an insight as resolved by the user."""
    ins = db.execute(select(CommitmentInsight).where(CommitmentInsight.id == insight_id)).scalars().first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    now = datetime.now(timezone.utc)
    ins.status = "resolved"
    ins.resolved_at = now
    ins.updated_at = now

    audit = AuditEvent(
        id=uuid.uuid4(),
        user_id=ins.user_id,
        entity_type="commitment_insight",
        entity_id=ins.id,
        action="resolve",
        actor_type="user",
        after_summary={"status": ins.status, "action": payload.resolution_action, "notes": payload.notes},
        created_at=now,
    )
    db.add(audit)
    db.commit()
    db.refresh(ins)

    return _to_insight_response(ins)
