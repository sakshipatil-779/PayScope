"""Orchestrator managing Cancellation Case lifecycle and state transitions."""
from datetime import datetime, timezone
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.analytics.cancellations.config import ALL_PLAYBOOKS
from app.analytics.cancellations.instruction_builder import build_cancellation_checklist
from app.analytics.cancellations.mechanism_classifier import classify_payment_mechanism
from app.analytics.cancellations.playbook_resolver import resolve_playbook
from app.analytics.cancellations.schemas import (
    CancellationCaseResponse,
    CancellationCaseStatus,
    CancellationEligibilityResponse,
    PaymentMechanism,
    Playbook,
)
from app.models.cancellation_case import CancellationCase
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.merchant import Merchant


class CancellationOrchestrator:
    """Coordinates cancellation cases, ensuring user-guided informational operations only."""

    def __init__(self, db: Session):
        self.db = db

    def get_playbooks(self) -> List[Playbook]:
        """Returns all registered playbooks."""
        return ALL_PLAYBOOKS

    def check_eligibility(
        self,
        commitment_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CancellationEligibilityResponse:
        """Determines payment mechanism and recommended playbook for a commitment."""
        commitment = self.db.execute(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found for user {user_id}")

        transactions = list(commitment.transactions or [])
        detected_mechanism, confidence = classify_payment_mechanism(commitment, transactions)
        playbook = resolve_playbook(detected_mechanism, commitment=commitment, merchant=commitment.merchant)

        available_mechanisms = [
            PaymentMechanism.UPI_AUTOPAY,
            PaymentMechanism.CARD_SI,
            PaymentMechanism.E_NACH,
            PaymentMechanism.OTHER,
        ]

        merchant_name = commitment.merchant.canonical_name if commitment.merchant else None

        return CancellationEligibilityResponse(
            commitment_id=commitment.id,
            commitment_name=commitment.display_name,
            merchant_id=commitment.merchant_id,
            merchant_name=merchant_name,
            detected_mechanism=detected_mechanism,
            confidence=confidence,
            available_mechanisms=available_mechanisms,
            recommended_playbook=playbook,
        )

    def create_or_get_case(
        self,
        user_id: uuid.UUID,
        commitment_id: uuid.UUID,
        payment_mechanism: Optional[PaymentMechanism] = None,
        playbook_key: Optional[str] = None,
        user_notes: Optional[str] = None,
    ) -> CancellationCase:
        """Finds existing active case or creates a new one."""
        existing_case = self.db.execute(
            select(CancellationCase).where(
                CancellationCase.commitment_id == commitment_id,
                CancellationCase.user_id == user_id,
                CancellationCase.status.not_in([CancellationCaseStatus.CLOSED.value]),
            )
        ).scalar_one_or_none()

        if existing_case:
            return existing_case

        commitment = self.db.execute(
            select(Commitment).where(
                Commitment.id == commitment_id,
                Commitment.user_id == user_id,
            )
        ).scalar_one_or_none()

        if not commitment:
            raise ValueError(f"Commitment {commitment_id} not found for user {user_id}")

        if not payment_mechanism or payment_mechanism == PaymentMechanism.UNKNOWN:
            transactions = list(commitment.transactions or [])
            detected_mechanism, _ = classify_payment_mechanism(commitment, transactions)
            payment_mechanism = detected_mechanism

        resolved_pb = resolve_playbook(
            payment_mechanism,
            commitment=commitment,
            merchant=commitment.merchant,
            playbook_key=playbook_key,
        )

        new_case = CancellationCase(
            user_id=user_id,
            commitment_id=commitment_id,
            merchant_id=commitment.merchant_id,
            payment_mechanism=payment_mechanism.value,
            playbook_key=resolved_pb.playbook_key,
            status=CancellationCaseStatus.NOT_STARTED.value,
            completed_steps=[],
            user_notes=user_notes,
        )
        self.db.add(new_case)
        self.db.commit()
        self.db.refresh(new_case)
        return new_case

    def get_case(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[CancellationCase]:
        """Fetches a specific cancellation case enforcing user ownership."""
        return self.db.execute(
            select(CancellationCase).where(
                CancellationCase.id == case_id,
                CancellationCase.user_id == user_id,
            )
        ).scalar_one_or_none()

    def list_cases(
        self,
        user_id: uuid.UUID,
    ) -> List[CancellationCase]:
        """Lists all cancellation cases for a user."""
        return list(
            self.db.execute(
                select(CancellationCase)
                .where(CancellationCase.user_id == user_id)
                .order_by(CancellationCase.created_at.desc())
            ).scalars().all()
        )

    def start_case(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CancellationCase:
        """Transitions case to IN_PROGRESS."""
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        if case.status == CancellationCaseStatus.NOT_STARTED.value:
            case.status = CancellationCaseStatus.IN_PROGRESS.value
            self.db.commit()
            self.db.refresh(case)
        return case

    def complete_step(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        step_id: str,
    ) -> CancellationCase:
        """Records a step completed by the user."""
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        current_steps = list(case.completed_steps or [])
        if step_id not in current_steps:
            current_steps.append(step_id)
            case.completed_steps = current_steps
            if case.status == CancellationCaseStatus.NOT_STARTED.value:
                case.status = CancellationCaseStatus.IN_PROGRESS.value
            self.db.commit()
            self.db.refresh(case)
        return case

    def report_cancelled(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        cancellation_date: Optional[datetime] = None,
        evidence_references: Optional[str] = None,
        user_notes: Optional[str] = None,
    ) -> CancellationCase:
        """Records that the user reported cancelling the commitment.

        Creates or links a Phase 6 CancellationEvent for automated post-cancellation charge monitoring.
        """
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        now = datetime.now(timezone.utc)
        case.status = CancellationCaseStatus.USER_REPORTED_CANCELLED.value
        case.user_reported_at = cancellation_date or now
        if evidence_references:
            case.evidence_references = evidence_references
        if user_notes:
            case.user_notes = user_notes

        # Create or link Phase 6 CancellationEvent
        if not case.cancellation_event_id:
            canc_event = CancellationEvent(
                user_id=user_id,
                commitment_id=case.commitment_id,
                merchant_id=case.merchant_id,
                event_timestamp=case.user_reported_at,
                event_source="user_recorded",
                confirmation_type="user_confirmed",
                evidence_description=(
                    evidence_references
                    or f"User reported cancellation via PayScope Cancellation Centre (Case: {case.id})"
                ),
                is_synthetic=True,
            )
            self.db.add(canc_event)
            self.db.flush()
            case.cancellation_event_id = canc_event.id

        self.db.commit()
        self.db.refresh(case)
        return case

    def submit_evidence(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        evidence_text: str,
        evidence_url_or_ref: Optional[str] = None,
    ) -> CancellationCase:
        """Stores evidence references submitted by user."""
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        combined_ref = evidence_text
        if evidence_url_or_ref:
            combined_ref += f" [Ref: {evidence_url_or_ref}]"

        case.evidence_references = combined_ref
        self.db.commit()
        self.db.refresh(case)
        return case

    def verify_case(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        verification_notes: str,
    ) -> CancellationCase:
        """Marks case as VERIFIED_CANCELLED with objective notes."""
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        now = datetime.now(timezone.utc)
        case.status = CancellationCaseStatus.VERIFIED_CANCELLED.value
        case.verified_at = now
        case.verification_notes = verification_notes

        if case.cancellation_event:
            case.cancellation_event.confirmation_type = "provider_confirmed"

        self.db.commit()
        self.db.refresh(case)
        return case

    def close_case(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> CancellationCase:
        """Closes a cancellation case."""
        case = self.get_case(case_id, user_id)
        if not case:
            raise ValueError("Cancellation case not found.")

        case.status = CancellationCaseStatus.CLOSED.value
        self.db.commit()
        self.db.refresh(case)
        return case

    def build_case_response(self, case: CancellationCase) -> CancellationCaseResponse:
        """Serializes case into complete response with playbook details."""
        commitment_name = case.commitment.display_name if case.commitment else "Commitment"
        merchant_name = case.merchant.canonical_name if case.merchant else None

        # Resolve playbook
        mechanism = PaymentMechanism(case.payment_mechanism) if case.payment_mechanism in PaymentMechanism._value2member_map_ else PaymentMechanism.OTHER
        pb = resolve_playbook(
            mechanism,
            commitment=case.commitment,
            merchant=case.merchant,
            playbook_key=case.playbook_key,
        )

        checklist = build_cancellation_checklist(pb, case.completed_steps or [])
        decorated_pb = Playbook(
            playbook_key=pb.playbook_key,
            title=pb.title,
            payment_mechanism=pb.payment_mechanism,
            guidance_type=pb.guidance_type,
            official_source_url=pb.official_source_url,
            source_verification_date=pb.source_verification_date,
            region=pb.region,
            summary=pb.summary,
            important_warnings=pb.important_warnings,
            steps=checklist,
            friction_level=pb.friction_level,
            friction_notes=pb.friction_notes,
        )

        return CancellationCaseResponse(
            id=case.id,
            user_id=case.user_id,
            commitment_id=case.commitment_id,
            commitment_name=commitment_name,
            merchant_id=case.merchant_id,
            merchant_name=merchant_name,
            payment_mechanism=mechanism,
            playbook_key=case.playbook_key,
            status=CancellationCaseStatus(case.status),
            completed_steps=case.completed_steps or [],
            user_notes=case.user_notes,
            evidence_references=case.evidence_references,
            user_reported_at=case.user_reported_at,
            verified_at=case.verified_at,
            verification_notes=case.verification_notes,
            created_at=case.created_at,
            updated_at=case.updated_at,
            playbook=decorated_pb,
        )
