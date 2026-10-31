"""Financial Impact & Savings Intelligence package."""
from app.analytics.financial_impact.category_analysis import get_user_category_analysis
from app.analytics.financial_impact.commitment_costs import (
    get_user_commitment_costs,
    is_confirmed_commitment,
)
from app.analytics.financial_impact.config import (
    SAVINGS_CLASS_POTENTIAL,
    SAVINGS_CLASS_REALIZED,
    SAVINGS_CLASS_USER_SELECTED,
)
from app.analytics.financial_impact.historical_spend import get_user_historical_spend
from app.analytics.financial_impact.impact_summary import get_user_financial_summary
from app.analytics.financial_impact.merchant_analysis import get_user_merchant_analysis
from app.analytics.financial_impact.normalization import (
    calculate_normalized_costs,
    round_currency,
)
from app.analytics.financial_impact.savings_calculator import (
    calculate_what_if_projection,
    get_user_savings_opportunities,
    get_user_savings_summary,
)
from app.analytics.financial_impact.schemas import (
    CategoryCostBreakdown,
    CommitmentCostItem,
    FinancialSummaryResponse,
    HistoricalPeriodSpend,
    HistoricalSpendResponse,
    MerchantCostRanking,
    MonthlyTrendPoint,
    SavingsCalculateRequest,
    SavingsCalculateResponse,
    SavingsOpportunityItem,
    SavingsScenarioCreateRequest,
    SavingsScenarioResponse,
    SavingsScenarioUpdateRequest,
    SavingsSummaryResponse,
    UpcomingExpenditureResponse,
    UpcomingExpenseItem,
)
from app.analytics.financial_impact.upcoming import get_user_upcoming_expenditure

__all__ = [
    "calculate_normalized_costs",
    "calculate_what_if_projection",
    "get_user_category_analysis",
    "get_user_commitment_costs",
    "get_user_financial_summary",
    "get_user_historical_spend",
    "get_user_merchant_analysis",
    "get_user_savings_opportunities",
    "get_user_savings_summary",
    "get_user_upcoming_expenditure",
    "is_confirmed_commitment",
    "round_currency",
    "SAVINGS_CLASS_POTENTIAL",
    "SAVINGS_CLASS_REALIZED",
    "SAVINGS_CLASS_USER_SELECTED",
    "CategoryCostBreakdown",
    "CommitmentCostItem",
    "FinancialSummaryResponse",
    "HistoricalPeriodSpend",
    "HistoricalSpendResponse",
    "MerchantCostRanking",
    "MonthlyTrendPoint",
    "SavingsCalculateRequest",
    "SavingsCalculateResponse",
    "SavingsOpportunityItem",
    "SavingsScenarioCreateRequest",
    "SavingsScenarioResponse",
    "SavingsScenarioUpdateRequest",
    "SavingsSummaryResponse",
    "UpcomingExpenditureResponse",
    "UpcomingExpenseItem",
]

