"""Pydantic schemas for Phase 6 commitment insights and anomaly intelligence."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class EvidenceItemResponse(BaseModel):
    """API response model for an evidence item supporting an insight."""
    id: uuid.UUID
    insight_id: uuid.UUID
    evidence_type: str
    role: str
    weight: Optional[Decimal] = None
    summary: str
    timestamp: Optional[datetime] = None
    transaction_id: Optional[uuid.UUID] = None
    notification_id: Optional[uuid.UUID] = None
    usage_coverage_id: Optional[uuid.UUID] = None
    usage_event_id: Optional[uuid.UUID] = None
    cancellation_event_id: Optional[uuid.UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PriceEventResponse(BaseModel):
    """API response model for a structured price change event."""
    id: uuid.UUID
    commitment_id: uuid.UUID
    event_type: str
    previous_amount: Decimal
    new_amount: Decimal
    currency: str
    absolute_change: Decimal
    percentage_change: Decimal
    effective_or_detected_at: datetime
    confidence_band: str
    explanation: Optional[str] = None
    detector_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightResponse(BaseModel):
    """API response model for a commitment insight."""
    id: uuid.UUID
    user_id: uuid.UUID
    commitment_id: uuid.UUID
    commitment_name: Optional[str] = None
    merchant_name: Optional[str] = None
    insight_type: str
    severity: str
    status: str
    title: str
    summary: str
    explanation: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    confidence_band: str
    detected_at: datetime
    detector_version: str
    user_action: Optional[str] = None
    user_action_at: Optional[datetime] = None
    user_notes: Optional[str] = None
    evidence_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InsightDetailResponse(InsightResponse):
    """Full detail response model for an insight including evidence and commitment context."""
    commitment_representative_amount: Optional[Decimal] = None
    commitment_cadence: Optional[str] = None
    price_event: Optional[PriceEventResponse] = None
    evidence_items: List[EvidenceItemResponse] = []


class InsightSummaryResponse(BaseModel):
    """Aggregated metrics and distribution summary across all insights for a user."""
    total_open: int
    price_increases: int
    trial_conversions: int
    potentially_unused: int
    post_cancellation_charges: int
    unusual_amounts: int
    high_severity: int
    medium_severity: int
    low_severity: int
    estimated_monthly_impact: Decimal


class InsightDetectionSummary(BaseModel):
    """Summary of a freshly executed intelligence detection run."""
    status: str
    total_detected: int
    price_increases_detected: int
    trial_conversions_detected: int
    potentially_unused_detected: int
    post_cancellation_charges_detected: int
    unusual_amounts_detected: int
    duration_ms: float
    insights: List[InsightResponse] = []


class InsightAcknowledgeRequest(BaseModel):
    """Request payload to acknowledge an insight."""
    notes: Optional[str] = None


class InsightDismissRequest(BaseModel):
    """Request payload to dismiss an insight."""
    reason: Optional[str] = None
    notes: Optional[str] = None


class InsightResolveRequest(BaseModel):
    """Request payload to mark an insight resolved."""
    resolution_action: Optional[str] = None
    notes: Optional[str] = None

