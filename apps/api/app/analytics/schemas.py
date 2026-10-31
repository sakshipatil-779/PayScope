"""Pydantic schemas for recurring commitment discovery, review, and management."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CommitmentBase(BaseModel):
    """Base fields for a commitment."""
    display_name: str
    commitment_type: str
    cadence: str
    amount_pattern: str
    status: str
    currency: str = "INR"
    representative_amount: Optional[Decimal] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    first_seen_at: datetime
    last_seen_at: datetime
    next_expected_date: Optional[date] = None
    annualised_amount: Optional[Decimal] = None
    annualisation_method: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    confidence_band: str
    detection_reason_codes: Optional[List[str]] = None
    detection_explanation: Optional[str] = None
    detector_version: str
    user_decision: Optional[str] = None
    user_decision_at: Optional[datetime] = None


class CommitmentResponse(CommitmentBase):
    """API response model for a single commitment."""
    id: uuid.UUID
    user_id: uuid.UUID
    merchant_id: Optional[uuid.UUID] = None
    transaction_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommitmentTransactionEvidence(BaseModel):
    """Supporting transaction evidence item."""
    id: uuid.UUID
    transaction_id: uuid.UUID
    relationship_role: str
    match_confidence: Optional[Decimal] = None
    reason: Optional[str] = None
    transaction_date: datetime
    raw_descriptor: str
    normalised_descriptor: Optional[str] = None
    amount: Decimal
    currency: str
    payment_channel: str
    payment_reference: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CommitmentDetailResponse(CommitmentResponse):
    """Full detail response including supporting transactions and merchant info."""
    supporting_transactions: List[CommitmentTransactionEvidence] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    """Chronological event in a commitment's history."""
    event_id: str
    event_date: datetime
    event_type: str  # transaction, notification, price_change, user_decision
    title: str
    description: str
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    payment_channel: Optional[str] = None
    payment_reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CommitmentTimelineResponse(BaseModel):
    """Timeline of all historical events and debits for a commitment."""
    commitment_id: uuid.UUID
    display_name: str
    events: List[TimelineEvent]


class CommitmentUpdateRequest(BaseModel):
    """User correction request payload for a commitment."""
    display_name: Optional[str] = None
    commitment_type: Optional[str] = None  # subscription, membership, utility, insurance, loan_emi, other
    cadence: Optional[str] = None          # weekly, fortnightly, monthly, quarterly, annual, variable_monthly, irregular


class CommitmentSummaryResponse(BaseModel):
    """Summary metrics for all commitments of the current user."""
    total_commitments: int
    active_commitments: int
    candidate_commitments: int
    review_required_commitments: int
    confirmed_commitments: int
    total_monthly_spend: Decimal
    total_annualised_spend: Decimal
    by_cadence: Dict[str, int]
    by_commitment_type: Dict[str, int]
    by_confidence_band: Dict[str, int]


class DiscoveryResultResponse(BaseModel):
    """Response returned upon completing discovery execution."""
    total_discovered: int
    active_count: int
    candidate_count: int
    needs_review_count: int
    message: str
