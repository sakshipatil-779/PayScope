"""Schemas for merchant intelligence resolution, review items, and aliases."""
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


@dataclass
class MatchCandidate:
    """A scored candidate merchant during resolution."""

    merchant_id: uuid.UUID
    canonical_name: str
    category: str
    score: float
    method: str
    confidence_band: str
    matched_alias: Optional[str] = None
    matched_alias_id: Optional[uuid.UUID] = None


@dataclass
class MatchResolutionResult:
    """Comprehensive outcome of descriptor resolution."""

    raw_descriptor: str
    normalised_descriptor: str
    status: str  # MATCHED_HIGH, MATCHED_MEDIUM, NEEDS_REVIEW, UNRESOLVED, USER_CONFIRMED
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    matched_alias_id: Optional[uuid.UUID] = None
    match_method: Optional[str] = None
    score: float = 0.0
    confidence_band: str = "none"  # high, medium, low, none
    explanation: str = ""
    is_ambiguous: bool = False
    candidates: List[MatchCandidate] = field(default_factory=list)


# --- Pydantic API Schemas ---


class ResolveDescriptorRequest(BaseModel):
    """Input request to resolve a raw descriptor."""

    raw_descriptor: str = Field(..., min_length=1, max_length=500, description="Raw transaction descriptor to resolve")


class CandidateMerchantResponse(BaseModel):
    """Candidate merchant item in resolution response."""

    merchant_id: uuid.UUID
    canonical_name: str
    category: str
    score: float
    method: str
    confidence_band: str


class ResolveDescriptorResponse(BaseModel):
    """Diagnostic and preview resolution response."""

    raw_descriptor: str
    normalised_descriptor: str
    status: str
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: Optional[str] = None
    category: Optional[str] = None
    match_method: Optional[str] = None
    score: float
    confidence_band: str
    explanation: str
    is_ambiguous: bool
    candidates: List[CandidateMerchantResponse] = []


class MerchantResponse(BaseModel):
    """Merchant detail response."""

    id: uuid.UUID
    canonical_name: str
    category: str
    commitment_type_default: Optional[str] = None
    website_url: Optional[str] = None
    support_url: Optional[str] = None
    is_fictional_demo_merchant: bool
    reference_source: Optional[str] = None
    alias_count: int = 0
    transaction_count: int = 0
    created_at: datetime
    updated_at: datetime


class DescriptorAliasResponse(BaseModel):
    """Descriptor alias response."""

    id: uuid.UUID
    merchant_id: uuid.UUID
    alias_text: str
    normalised_alias: str
    matcher_type: str
    pattern: Optional[str] = None
    confidence_band: str
    reference_source: Optional[str] = None
    verified_at: Optional[date] = None
    is_active: bool
    created_at: datetime


class CreateAliasRequest(BaseModel):
    """Payload to add an alias to a merchant."""

    merchant_id: uuid.UUID
    alias_text: str = Field(..., min_length=1, max_length=255)
    matcher_type: str = Field("exact", description="exact, prefix, regex, token_pattern")
    pattern: Optional[str] = None
    confidence_band: str = Field("high", description="high, medium, low")


class UpdateAliasRequest(BaseModel):
    """Payload to update an alias."""

    matcher_type: Optional[str] = None
    pattern: Optional[str] = None
    confidence_band: Optional[str] = None
    is_active: Optional[bool] = None


class ManualReviewItemResponse(BaseModel):
    """Manual review item payload."""

    id: uuid.UUID
    user_id: uuid.UUID
    transaction_id: Optional[uuid.UUID] = None
    item_type: str
    raw_descriptor: str
    normalised_descriptor: str
    suggested_merchant_id: Optional[uuid.UUID] = None
    suggested_merchant_name: Optional[str] = None
    similarity_score: Optional[float] = None
    confidence_band: Optional[str] = None
    match_method: Optional[str] = None
    explanation: Optional[str] = None
    reason_code: str
    status: str
    candidates: Optional[List[Dict[str, Any]]] = None
    user_selected_merchant_id: Optional[uuid.UUID] = None
    decision_notes: Optional[str] = None
    created_at: datetime
    reviewed_at: Optional[datetime] = None


class CorrectReviewRequest(BaseModel):
    """User correction request for review item."""

    merchant_id: uuid.UUID
    create_alias: bool = False
    decision_notes: Optional[str] = None


class ReprocessRequest(BaseModel):
    """Payload for manual reprocessing of transactions."""

    force_all: bool = False  # If True, reprocesses non-confirmed matched items as well
