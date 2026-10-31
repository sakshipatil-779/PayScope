"""Commitment cost evaluation, normalized recurring spend, and confirmed vs candidate classification."""
import uuid
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.analytics.financial_impact.config import (
    CANDIDATE_STATUSES,
    CONFIRMED_CONFIDENCE_BANDS,
    CONFIRMED_STATUSES,
    INACTIVE_STATUSES,
)
from app.analytics.financial_impact.normalization import calculate_normalized_costs
from app.analytics.financial_impact.schemas import CommitmentCostItem
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.transaction import Transaction


def is_confirmed_commitment(c: Commitment) -> bool:
    """Determine whether a commitment qualifies as a confirmed recurring obligation.
    
    Rules:
    - Status must be active or user_confirmed.
    - Confidence band must be high or medium.
    - Cadence cannot be irregular or unknown.
    - Status cannot be candidate or review_required.
    """
    if c.status in CANDIDATE_STATUSES or c.status in INACTIVE_STATUSES:
        return False
    if c.status not in CONFIRMED_STATUSES:
        return False
    if c.confidence_band not in CONFIRMED_CONFIDENCE_BANDS:
        return False
    if (c.cadence or "").lower() in ("irregular", "unknown"):
        return False
    return True


def get_user_commitment_costs(
    db: Session,
    user_id: uuid.UUID,
) -> List[CommitmentCostItem]:
    """Calculate normalized monthly and annual costs for all user commitments.
    
    Includes canonical merchant lookup, linked transaction history, and
    clear separation of confirmed vs candidate obligations.
    """
    # Fetch commitments with merchant relation
    stmt = (
        select(Commitment)
        .options(joinedload(Commitment.merchant))
        .where(Commitment.user_id == user_id)
        .order_by(Commitment.representative_amount.desc())
    )
    commitments = db.scalars(stmt).unique().all()

    # Pre-fetch transaction amounts and counts per commitment
    tx_stats_stmt = (
        select(
            CommitmentTransaction.commitment_id,
            func.count(Transaction.id).label("tx_count"),
            func.array_agg(Transaction.amount).label("amounts"),
        )
        .join(Transaction, CommitmentTransaction.transaction_id == Transaction.id)
        .where(
            Transaction.user_id == user_id,
            Transaction.direction.ilike("debit"),
            Transaction.transaction_status.ilike("successful"),
        )
        .group_by(CommitmentTransaction.commitment_id)
    )
    tx_stats = db.execute(tx_stats_stmt).all()
    tx_stat_map = {row.commitment_id: (row.tx_count, row.amounts) for row in tx_stats}

    items: List[CommitmentCostItem] = []
    for c in commitments:
        tx_count, amounts = tx_stat_map.get(c.id, (0, []))
        hist_amounts = [Decimal(str(a)) for a in (amounts or [])]

        monthly_cost, annual_cost, calc_method = calculate_normalized_costs(
            amount=c.representative_amount or Decimal("0.00"),
            cadence=c.cadence,
            historical_amounts=hist_amounts,
        )

        confirmed = is_confirmed_commitment(c)
        candidate = c.status in CANDIDATE_STATUSES or not confirmed

        merchant_name = c.merchant.canonical_name if c.merchant else c.display_name

        items.append(
            CommitmentCostItem(
                commitment_id=c.id,
                merchant_id=c.merchant_id,
                merchant_name=merchant_name,
                display_name=c.display_name,
                commitment_type=c.commitment_type,
                cadence=c.cadence,
                amount_pattern=c.amount_pattern,
                representative_amount=c.representative_amount or Decimal("0.00"),
                currency=c.currency or "INR",
                normalized_monthly_cost=monthly_cost,
                annualized_cost=annual_cost,
                calculation_method=calc_method,
                confidence_band=c.confidence_band,
                status=c.status,
                is_confirmed=confirmed,
                is_candidate=candidate,
                next_expected_date=c.next_expected_date,
                transaction_count=tx_count,
            )
        )

    return items

