"""Database synchronization layer for persisting discovered commitments idempotently."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.analytics.amount_analyzer import AmountAnalysis
from app.analytics.cadence_classifier import CadenceClassification
from app.analytics.confidence import ConfidenceAssessment
from app.analytics.config import DETECTOR_VERSION
from app.analytics.date_utils import estimate_next_expected_date
from app.analytics.evidence_builder import build_commitment_evidence
from app.analytics.interval_analyzer import IntervalAnalysis
from app.analytics.transaction_grouper import TransactionStream
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction


def calculate_annualised_amount(
    representative_amount: Optional[Decimal],
    cadence: str,
    median_interval_days: float = 0.0,
) -> Tuple[Optional[Decimal], Optional[str]]:
    """Compute annualised obligation amount based on cadence."""
    if not representative_amount or representative_amount <= Decimal("0.00"):
        return None, None

    if cadence == "weekly":
        return round(representative_amount * Decimal("52"), 2), "weekly_x_52"
    elif cadence == "fortnightly":
        return round(representative_amount * Decimal("26"), 2), "fortnightly_x_26"
    elif cadence in ("monthly", "variable_monthly"):
        return round(representative_amount * Decimal("12"), 2), "monthly_x_12"
    elif cadence == "quarterly":
        return round(representative_amount * Decimal("4"), 2), "quarterly_x_4"
    elif cadence == "annual":
        return round(representative_amount, 2), "annual_x_1"
    elif cadence == "irregular" and median_interval_days > 0:
        multiplier = Decimal(str(round(365.25 / median_interval_days, 4)))
        return round(representative_amount * multiplier, 2), "annual_estimated_by_interval"

    return None, None


def sync_commitment_to_db(
    db: Session,
    stream: TransactionStream,
    cadence_res: CadenceClassification,
    interval_info: IntervalAnalysis,
    amount_info: AmountAnalysis,
    confidence_assessment: ConfidenceAssessment,
    commitment_type: str,
) -> Commitment:
    """Idempotently sync or update a single commitment record and its evidence links.
    
    Safety guarantees:
    - Never duplicate commitments for the same stream.
    - Never overwrite user confirmations or corrections (user_decision).
    - Idempotently link transaction evidence.
    
    Args:
        db: SQLAlchemy database session.
        stream: Clustered transaction stream.
        cadence_res: Cadence classification result.
        interval_info: Interval metrics.
        amount_info: Amount metrics.
        confidence_assessment: Confidence scores and codes.
        commitment_type: Inferred commitment type.
        
    Returns:
        Persisted or updated Commitment model instance.
    """
    now = datetime.now(timezone.utc)
    user_id = stream.user_id
    merchant_id = stream.merchant_id
    curr = stream.currency
    display_name = stream.display_name

    # Step 1: Look for existing commitment
    query = select(Commitment).where(
        Commitment.user_id == user_id,
        Commitment.currency == curr,
    )
    if merchant_id is not None:
        query = query.where(Commitment.merchant_id == merchant_id)
    else:
        query = query.where(
            Commitment.merchant_id.is_(None),
            Commitment.display_name == display_name,
        )

    existing: Optional[Commitment] = db.execute(query).scalars().first()

    first_date = stream.transactions[0].transaction_date
    last_date = stream.transactions[-1].transaction_date
    med_days_int = int(round(interval_info.median_interval))
    next_date = estimate_next_expected_date(
        last_date.date() if isinstance(last_date, datetime) else last_date,
        cadence_res.cadence,
        med_days_int,
    )

    annual_amt, annual_method = calculate_annualised_amount(
        amount_info.representative_amount,
        cadence_res.cadence,
        interval_info.median_interval,
    )

    # Initial default status
    if cadence_res.is_candidate_only:
        default_status = "candidate"
    elif confidence_assessment.band == "needs_review":
        default_status = "review_required"
    else:
        default_status = "active"

    if existing:
        commitment = existing
        # ALWAYS update observation stats and evidence
        commitment.representative_amount = amount_info.representative_amount
        commitment.amount_min = amount_info.amount_min
        commitment.amount_max = amount_info.amount_max
        commitment.amount_pattern = amount_info.amount_pattern
        commitment.first_seen_at = first_date
        commitment.last_seen_at = last_date
        commitment.next_expected_date = next_date
        commitment.annualised_amount = annual_amt
        commitment.annualisation_method = annual_method
        commitment.confidence_score = confidence_assessment.score
        commitment.confidence_band = confidence_assessment.band
        commitment.detection_reason_codes = confidence_assessment.reason_codes
        commitment.detection_explanation = confidence_assessment.explanation
        commitment.detector_version = DETECTOR_VERSION
        commitment.updated_at = now

        # ONLY update user-mutable fields if user has NOT made a decision
        if not commitment.user_decision:
            commitment.display_name = display_name
            commitment.commitment_type = commitment_type
            commitment.cadence = cadence_res.cadence
            commitment.status = default_status
    else:
        commitment = Commitment(
            id=uuid.uuid4(),
            user_id=user_id,
            merchant_id=merchant_id,
            display_name=display_name,
            commitment_type=commitment_type,
            cadence=cadence_res.cadence,
            amount_pattern=amount_info.amount_pattern,
            status=default_status,
            currency=curr,
            representative_amount=amount_info.representative_amount,
            amount_min=amount_info.amount_min,
            amount_max=amount_info.amount_max,
            first_seen_at=first_date,
            last_seen_at=last_date,
            next_expected_date=next_date,
            annualised_amount=annual_amt,
            annualisation_method=annual_method,
            confidence_score=confidence_assessment.score,
            confidence_band=confidence_assessment.band,
            detection_reason_codes=confidence_assessment.reason_codes,
            detection_explanation=confidence_assessment.explanation,
            detector_version=DETECTOR_VERSION,
            user_decision=None,
            user_decision_at=None,
            created_at=now,
            updated_at=now,
        )
        db.add(commitment)
        db.flush()

    # Step 2: Idempotently sync supporting transactions
    # Fetch existing transaction IDs for this commitment
    existing_txn_ids_stmt = select(CommitmentTransaction.transaction_id).where(
        CommitmentTransaction.commitment_id == commitment.id
    )
    existing_txn_ids = set(db.execute(existing_txn_ids_stmt).scalars().all())

    evidence_records = build_commitment_evidence(commitment, stream.transactions)
    for ev in evidence_records:
        if ev.transaction_id not in existing_txn_ids:
            db.add(ev)
            existing_txn_ids.add(ev.transaction_id)

    return commitment
