"""Pydantic schemas for Phase 7 Financial Impact, Savings Intelligence, and What-If Projections."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CommitmentCostItem(BaseModel):
    """Normalized monthly and annual cost model for a single commitment."""
    commitment_id: uuid.UUID
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: str
    display_name: str
    commitment_type: str
    cadence: str
    amount_pattern: str
    representative_amount: Decimal
    currency: str = "INR"
    normalized_monthly_cost: Decimal
    annualized_cost: Decimal
    calculation_method: str
    confidence_band: str
    status: str
    is_confirmed: bool
    is_candidate: bool
    next_expected_date: Optional[date] = None
    transaction_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class FinancialSummaryResponse(BaseModel):
    """Top-level financial impact metrics."""
    currency: str = "INR"
    monthly_recurring_spend: Decimal
    annualized_recurring_spend: Decimal
    total_confirmed_commitments: int
    potential_candidate_annual_cost: Decimal
    total_candidate_commitments: int
    historical_spend_12m: Decimal
    upcoming_30d_expected_spend: Decimal
    potential_annual_savings: Decimal
    calculation_timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoricalPeriodSpend(BaseModel):
    """Summary of historical expenditure for a specific window."""
    period: str
    period_label: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    gross_debit_amount: Decimal
    total_credits: Decimal
    net_spend: Decimal
    transaction_count: int
    excluded_duplicates_count: int = 0
    excluded_failed_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class MonthlyTrendPoint(BaseModel):
    """Spend point in monthly timeline."""
    month_key: str  # YYYY-MM
    month_label: str
    gross_debit: Decimal
    credits: Decimal
    net_spend: Decimal
    recurring_debit: Decimal


class HistoricalSpendResponse(BaseModel):
    """Historical expenditure response across multiple periods."""
    currency: str = "INR"
    periods: List[HistoricalPeriodSpend]
    monthly_timeline: List[MonthlyTrendPoint]

    model_config = ConfigDict(from_attributes=True)


class CategoryCostBreakdown(BaseModel):
    """Category-level financial impact."""
    category: str
    category_label: str
    monthly_cost: Decimal
    annualized_cost: Decimal
    historical_spend_12m: Decimal
    percentage_of_recurring: Decimal
    commitment_count: int

    model_config = ConfigDict(from_attributes=True)


class MerchantCostRanking(BaseModel):
    """Canonical merchant expenditure ranking."""
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: str
    category: str
    monthly_cost: Decimal
    annualized_cost: Decimal
    historical_spend_12m: Decimal
    percentage_of_total: Decimal
    commitment_count: int
    aliases: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class UpcomingExpenseItem(BaseModel):
    """Individual upcoming expected commitment payment."""
    commitment_id: uuid.UUID
    display_name: str
    merchant_name: str
    expected_date: date
    estimated_amount: Decimal
    currency: str = "INR"
    cadence: str
    estimation_basis: str  # scheduled, estimated_cadence, historically_observed
    is_confirmed: bool

    model_config = ConfigDict(from_attributes=True)


class UpcomingExpenditureResponse(BaseModel):
    """Upcoming expected commitment charges."""
    currency: str = "INR"
    total_upcoming_30d: Decimal
    total_upcoming_60d: Decimal
    items: List[UpcomingExpenseItem]

    model_config = ConfigDict(from_attributes=True)


class SavingsOpportunityItem(BaseModel):
    """Single transparent savings opportunity."""
    id: str
    opportunity_type: str  # PRICE_INCREASE, POTENTIALLY_UNUSED, CATEGORY_DUPLICATE
    classification: str = "POTENTIAL"  # POTENTIAL, USER_SELECTED, REALIZED
    commitment_id: uuid.UUID
    commitment_name: str
    merchant_name: str
    category: str
    current_monthly_cost: Decimal
    current_annual_cost: Decimal
    potential_monthly_saving: Decimal
    potential_annual_saving: Decimal
    evidence_summary: str
    insight_id: Optional[uuid.UUID] = None
    price_event_id: Optional[uuid.UUID] = None
    usage_coverage_id: Optional[uuid.UUID] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SavingsSummaryResponse(BaseModel):
    """Complete savings opportunities summary."""
    currency: str = "INR"
    total_potential_annual_savings: Decimal
    total_potential_monthly_savings: Decimal
    price_increase_savings: Decimal
    unused_commitment_savings: Decimal
    duplicate_service_savings: Decimal
    opportunities_count: int
    opportunities: List[SavingsOpportunityItem]

    model_config = ConfigDict(from_attributes=True)


class SavingsCalculateRequest(BaseModel):
    """Request to calculate what-if projection for selected savings opportunities."""
    selected_opportunity_ids: List[str]


class SavingsCalculateResponse(BaseModel):
    """Projected expenditure outcomes after applying selected savings."""
    currency: str = "INR"
    baseline_annual_cost: Decimal
    selected_annual_savings: Decimal
    selected_monthly_savings: Decimal
    projected_annual_cost: Decimal
    projected_monthly_cost: Decimal
    percentage_reduction: Decimal
    selected_count: int
    safeguards_applied: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class SavingsScenarioCreateRequest(BaseModel):
    """Payload to persist a what-if savings scenario."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    selected_opportunity_ids: List[str]
    parameters: Optional[Dict[str, Any]] = None


class SavingsScenarioUpdateRequest(BaseModel):
    """Payload to update an existing scenario."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    selected_opportunity_ids: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None


class SavingsScenarioResponse(BaseModel):
    """Response model for a persisted savings scenario."""
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str] = None
    selected_opportunity_ids: List[str]
    selected_commitment_ids: List[str]
    baseline_annual_cost: Decimal
    projected_annual_cost: Decimal
    annual_savings: Decimal
    monthly_savings: Decimal
    percentage_reduction: Decimal
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

