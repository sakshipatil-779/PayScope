"""Pydantic schemas for the Mechanism-Aware Cancellation Centre."""
from datetime import datetime
from enum import Enum
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class PaymentMechanism(str, Enum):
    UPI_AUTOPAY = "UPI_AUTOPAY"
    E_NACH = "E_NACH"
    CARD_SI = "CARD_SI"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class CancellationCaseStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    GUIDANCE_REVIEWED = "GUIDANCE_REVIEWED"
    IN_PROGRESS = "IN_PROGRESS"
    USER_REPORTED_CANCELLED = "USER_REPORTED_CANCELLED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED_CANCELLED = "VERIFIED_CANCELLED"
    UNABLE_TO_COMPLETE = "UNABLE_TO_COMPLETE"
    CLOSED = "CLOSED"


class GuidanceType(str, Enum):
    MERCHANT_VERIFIED = "merchant_verified"
    GENERIC_MECHANISM = "generic_mechanism"


class FrictionLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class CancellationStep(BaseModel):
    id: str
    step_number: int
    title: str
    instruction: str
    action_type: str = "user_manual_action"
    warning: Optional[str] = None
    verification_tip: Optional[str] = None
    is_completed: bool = False


class Playbook(BaseModel):
    playbook_key: str
    title: str
    payment_mechanism: PaymentMechanism
    guidance_type: GuidanceType
    official_source_url: Optional[str] = None
    source_verification_date: Optional[str] = None
    region: str = "IN"
    summary: str
    important_warnings: List[str] = Field(default_factory=list)
    steps: List[CancellationStep] = Field(default_factory=list)
    friction_level: FrictionLevel = FrictionLevel.LOW
    friction_notes: Optional[str] = None


class CancellationEligibilityResponse(BaseModel):
    commitment_id: uuid.UUID
    commitment_name: str
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: Optional[str] = None
    detected_mechanism: PaymentMechanism
    confidence: float
    available_mechanisms: List[PaymentMechanism]
    recommended_playbook: Playbook


class CancellationCaseCreate(BaseModel):
    commitment_id: uuid.UUID
    payment_mechanism: Optional[PaymentMechanism] = None
    playbook_key: Optional[str] = None
    user_notes: Optional[str] = None


class CancellationCaseUpdate(BaseModel):
    user_notes: Optional[str] = None
    evidence_references: Optional[str] = None
    status: Optional[CancellationCaseStatus] = None


class CancellationStepCompleteRequest(BaseModel):
    step_id: str


class CancellationReportRequest(BaseModel):
    cancellation_date: Optional[datetime] = None
    evidence_references: Optional[str] = None
    user_notes: Optional[str] = None


class CancellationEvidenceSubmitRequest(BaseModel):
    evidence_text: str
    evidence_url_or_ref: Optional[str] = None


class CancellationCaseResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    commitment_id: uuid.UUID
    commitment_name: str
    merchant_id: Optional[uuid.UUID] = None
    merchant_name: Optional[str] = None
    payment_mechanism: PaymentMechanism
    playbook_key: str
    status: CancellationCaseStatus
    completed_steps: List[str]
    user_notes: Optional[str] = None
    evidence_references: Optional[str] = None
    user_reported_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    verification_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    playbook: Optional[Playbook] = None

    model_config = ConfigDict(from_attributes=True)
