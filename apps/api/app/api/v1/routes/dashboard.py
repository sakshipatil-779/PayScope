"""Dashboard summary aggregation API endpoint."""
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.financial_impact import (
    get_user_financial_summary,
    get_user_historical_spend,
    get_user_savings_summary,
    get_user_upcoming_expenditure,
)
from app.db.session import get_db
from app.models.cancellation_case import CancellationCase
from app.models.commitment import Commitment
from app.models.commitment_insight import CommitmentInsight
from app.models.manual_review_item import ManualReviewItem
from app.models.merchant import Merchant
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


class DashboardKPIs(BaseModel):
    active_commitments_count: int
    monthly_recurring_spend: Decimal
    annualized_recurring_spend: Decimal
    open_insights_count: int
    potential_annual_savings: Decimal
    cancellations_attention_count: int


class DashboardTopCommitment(BaseModel):
    id: uuid.UUID
    display_name: str
    merchant_name: Optional[str] = None
    category: str
    cadence: str
    monthly_cost: Decimal
    status: str
    confidence_band: str


class DashboardRecentInsight(BaseModel):
    id: uuid.UUID
    commitment_id: uuid.UUID
    commitment_name: str
    insight_type: str
    severity: str
    title: str
    summary: str


class DashboardFinancialOverview(BaseModel):
    monthly_recurring_spend: Decimal
    annualized_recurring_spend: Decimal
    upcoming_month_expected: Decimal
    candidate_annual_cost: Decimal
    historical_months: List[str]
    historical_amounts: List[Decimal]


class DashboardSummaryResponse(BaseModel):
    kpis: DashboardKPIs
    financial_overview: DashboardFinancialOverview
    top_commitments: List[DashboardTopCommitment]
    category_distribution: Dict[str, Decimal]
    recent_insights: List[DashboardRecentInsight]
    insight_type_counts: Dict[str, int]
    cancellation_summary: Dict[str, int]
    merchant_review_pending: int
    canonical_merchants_count: int


def _resolve_user_id(db: Session, user_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    if user_id:
        return user_id
    user = UserRepository.get_or_create_demo_user(db)
    return user.id


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    user_id: Optional[uuid.UUID] = Query(None, description="Workspace user UUID"),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Aggregates all real metrics across commitments, financial impact, insights, savings, and cancellations."""
    target_user_id = _resolve_user_id(db, user_id)

    # 1. Financial summary & savings summary
    fin_summary = get_user_financial_summary(db, target_user_id)
    savings_summary = get_user_savings_summary(db, target_user_id)
    upcoming = get_user_upcoming_expenditure(db, target_user_id)
    history = get_user_historical_spend(db, target_user_id)

    # 2. Insights
    insights = list(
        db.execute(
            select(CommitmentInsight)
            .join(Commitment, CommitmentInsight.commitment_id == Commitment.id)
            .where(
                Commitment.user_id == target_user_id,
                CommitmentInsight.status == "open",
            )
            .order_by(CommitmentInsight.detected_at.desc())
        ).scalars().all()
    )

    insight_counts: Dict[str, int] = {
        "price_increase": 0,
        "trial_conversion": 0,
        "potentially_unused": 0,
        "post_cancellation_charge": 0,
        "unusual_amount": 0,
    }
    recent_insights_list: List[DashboardRecentInsight] = []

    for ins in insights:
        itype = ins.insight_type
        if itype in insight_counts:
            insight_counts[itype] += 1
        else:
            insight_counts[itype] = 1

        if len(recent_insights_list) < 5:
            recent_insights_list.append(
                DashboardRecentInsight(
                    id=ins.id,
                    commitment_id=ins.commitment_id,
                    commitment_name=ins.commitment.display_name if ins.commitment else "Commitment",
                    insight_type=ins.insight_type,
                    severity=ins.severity,
                    title=ins.title,
                    summary=ins.summary,
                )
            )

    # 3. Commitments
    all_commitments = list(
        db.execute(
            select(Commitment)
            .where(Commitment.user_id == target_user_id)
            .order_by(Commitment.representative_amount.desc().nullslast())
        ).scalars().all()
    )

    top_commitments_list: List[DashboardTopCommitment] = []
    category_distribution: Dict[str, Decimal] = {}

    for c in all_commitments:
        if c.status in ("active", "confirmed", "user_confirmed"):
            cat = (c.merchant.category if c.merchant and c.merchant.category else c.commitment_type).capitalize()
            # Calculate monthly cost
            amt = c.representative_amount or Decimal("0.00")
            monthly_val = amt
            if c.cadence == "annual":
                monthly_val = round(amt / 12, 2)
            elif c.cadence == "weekly":
                monthly_val = round(amt * 52 / 12, 2)
            elif c.cadence == "quarterly":
                monthly_val = round(amt / 3, 2)

            category_distribution[cat] = category_distribution.get(cat, Decimal("0.00")) + monthly_val

            if len(top_commitments_list) < 6:
                top_commitments_list.append(
                    DashboardTopCommitment(
                        id=c.id,
                        display_name=c.display_name,
                        merchant_name=c.merchant.canonical_name if c.merchant else None,
                        category=cat,
                        cadence=c.cadence,
                        monthly_cost=monthly_val,
                        status=c.status,
                        confidence_band=c.confidence_band,
                    )
                )

    # 4. Cancellations
    cancellation_cases = list(
        db.execute(
            select(CancellationCase).where(CancellationCase.user_id == target_user_id)
        ).scalars().all()
    )

    canc_summary = {
        "total": len(cancellation_cases),
        "in_progress": sum(1 for c in cancellation_cases if c.status == "IN_PROGRESS"),
        "user_reported": sum(1 for c in cancellation_cases if c.status == "USER_REPORTED_CANCELLED"),
        "verified_cancelled": sum(1 for c in cancellation_cases if c.status == "VERIFIED_CANCELLED"),
        "needs_attention": sum(1 for c in cancellation_cases if c.status in ("IN_PROGRESS", "USER_REPORTED_CANCELLED")),
    }

    # 5. Merchant review queue count & canonical count
    pending_reviews_count = db.execute(
        select(func.count(ManualReviewItem.id)).where(ManualReviewItem.status == "pending")
    ).scalar() or 0

    canonical_merchants_count = db.execute(
        select(func.count(Merchant.id))
    ).scalar() or 0

    kpis = DashboardKPIs(
        active_commitments_count=fin_summary.total_confirmed_commitments,
        monthly_recurring_spend=fin_summary.monthly_recurring_spend,
        annualized_recurring_spend=fin_summary.annualized_recurring_spend,
        open_insights_count=len(insights),
        potential_annual_savings=savings_summary.total_potential_annual_savings,
        cancellations_attention_count=canc_summary["needs_attention"],
    )

    financial_overview = DashboardFinancialOverview(
        monthly_recurring_spend=fin_summary.monthly_recurring_spend,
        annualized_recurring_spend=fin_summary.annualized_recurring_spend,
        upcoming_month_expected=upcoming.total_upcoming_30d,
        candidate_annual_cost=fin_summary.potential_candidate_annual_cost,
        historical_months=[p.period_label for p in history.periods],
        historical_amounts=[p.gross_debit_amount for p in history.periods],
    )

    return DashboardSummaryResponse(
        kpis=kpis,
        financial_overview=financial_overview,
        top_commitments=top_commitments_list,
        category_distribution=category_distribution,
        recent_insights=recent_insights_list,
        insight_type_counts=insight_counts,
        cancellation_summary=canc_summary,
        merchant_review_pending=pending_reviews_count,
        canonical_merchants_count=canonical_merchants_count,
    )
