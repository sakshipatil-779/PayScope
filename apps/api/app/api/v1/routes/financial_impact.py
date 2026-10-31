"""API endpoints for Phase 7 Financial Impact, Historical Spend, and Upcoming Obligations."""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.analytics.financial_impact import (
    CategoryCostBreakdown,
    CommitmentCostItem,
    FinancialSummaryResponse,
    HistoricalSpendResponse,
    MerchantCostRanking,
    UpcomingExpenditureResponse,
    get_user_category_analysis,
    get_user_commitment_costs,
    get_user_financial_summary,
    get_user_historical_spend,
    get_user_merchant_analysis,
    get_user_upcoming_expenditure,
)
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/financial-impact", tags=["Financial Impact"])


def _resolve_user_id(db: Session, user_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """Resolve explicit user_id or fallback to default workspace demo user."""
    if user_id:
        return user_id
    user = UserRepository.get_or_create_demo_user(db)
    return user.id


@router.get("/summary", response_model=FinancialSummaryResponse)
def get_financial_summary(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> FinancialSummaryResponse:
    """Get top-level recurring financial impact metrics, annualized costs, and potential savings."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_financial_summary(db, target_user_id)


@router.get("/commitments", response_model=List[CommitmentCostItem])
def get_commitment_costs(
    confirmed_only: bool = Query(False, description="Filter for confirmed recurring commitments only"),
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[CommitmentCostItem]:
    """Get normalized monthly and annualized costs for user commitments."""
    target_user_id = _resolve_user_id(db, user_id)
    costs = get_user_commitment_costs(db, target_user_id)
    if confirmed_only:
        return [c for c in costs if c.is_confirmed]
    return costs


@router.get("/history", response_model=HistoricalSpendResponse)
def get_historical_spend(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> HistoricalSpendResponse:
    """Get historical expenditure across 30d, 90d, 180d, 365d, and monthly trendline."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_historical_spend(db, target_user_id)


@router.get("/categories", response_model=List[CategoryCostBreakdown])
def get_category_breakdown(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[CategoryCostBreakdown]:
    """Get category-level recurring expenditure and percentage distribution."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_category_analysis(db, target_user_id)


@router.get("/merchants", response_model=List[MerchantCostRanking])
def get_merchant_rankings(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[MerchantCostRanking]:
    """Get canonical merchant cost rankings and alias aggregations."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_merchant_analysis(db, target_user_id)


@router.get("/upcoming", response_model=UpcomingExpenditureResponse)
def get_upcoming_expenditure(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> UpcomingExpenditureResponse:
    """Get expected recurring debit commitments for upcoming 30 and 60 days."""
    target_user_id = _resolve_user_id(db, user_id)
    return get_user_upcoming_expenditure(db, target_user_id)

