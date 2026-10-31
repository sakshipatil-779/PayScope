"""Aggregated financial summary orchestration across recurring costs, historical spend, and savings."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.analytics.financial_impact.commitment_costs import get_user_commitment_costs
from app.analytics.financial_impact.historical_spend import get_user_historical_spend
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.savings_calculator import get_user_savings_summary
from app.analytics.financial_impact.schemas import FinancialSummaryResponse
from app.analytics.financial_impact.upcoming import get_user_upcoming_expenditure


def get_user_financial_summary(
    db: Session,
    user_id: uuid.UUID,
) -> FinancialSummaryResponse:
    """Generate top-level financial impact metrics for workspace dashboard."""
    cost_items = get_user_commitment_costs(db, user_id)

    confirmed_items = [item for item in cost_items if item.is_confirmed]
    candidate_items = [item for item in cost_items if item.is_candidate]

    monthly_recurring = sum((item.normalized_monthly_cost for item in confirmed_items), Decimal("0.00"))
    annualized_recurring = sum((item.annualized_cost for item in confirmed_items), Decimal("0.00"))

    candidate_annual = sum((item.annualized_cost for item in candidate_items), Decimal("0.00"))

    # Historical 12m spend
    hist_resp = get_user_historical_spend(db, user_id)
    hist_12m_period = next((p for p in hist_resp.periods if p.period == "365d"), None)
    historical_12m = hist_12m_period.gross_debit_amount if hist_12m_period else Decimal("0.00")

    # Upcoming 30d spend
    upcoming_resp = get_user_upcoming_expenditure(db, user_id)
    upcoming_30d = upcoming_resp.total_upcoming_30d

    # Potential savings
    savings_resp = get_user_savings_summary(db, user_id)
    potential_savings = savings_resp.total_potential_annual_savings

    return FinancialSummaryResponse(
        currency="INR",
        monthly_recurring_spend=round_currency(monthly_recurring),
        annualized_recurring_spend=round_currency(annualized_recurring),
        total_confirmed_commitments=len(confirmed_items),
        potential_candidate_annual_cost=round_currency(candidate_annual),
        total_candidate_commitments=len(candidate_items),
        historical_spend_12m=round_currency(historical_12m),
        upcoming_30d_expected_spend=round_currency(upcoming_30d),
        potential_annual_savings=round_currency(potential_savings),
        calculation_timestamp=datetime.now(timezone.utc),
    )

