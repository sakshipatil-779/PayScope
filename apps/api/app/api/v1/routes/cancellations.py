"""API routes for Phase 8 Mechanism-Aware Cancellation Centre."""
from datetime import datetime
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.analytics.cancellations.cancellation_orchestrator import CancellationOrchestrator
from app.analytics.cancellations.schemas import (
    CancellationCaseCreate,
    CancellationCaseResponse,
    CancellationCaseUpdate,
    CancellationEligibilityResponse,
    CancellationEvidenceSubmitRequest,
    CancellationReportRequest,
    CancellationStepCompleteRequest,
    Playbook,
)
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/cancellations", tags=["Cancellation Centre"])


def _resolve_user_id(db: Session, user_id: Optional[uuid.UUID] = None) -> uuid.UUID:
    """Resolve explicit user_id or fallback to default workspace demo user."""
    if user_id:
        return user_id
    user = UserRepository.get_or_create_demo_user(db)
    return user.id


@router.get("/playbooks", response_model=List[Playbook])
def list_cancellation_playbooks(
    db: Session = Depends(get_db),
) -> List[Playbook]:
    """Retrieve all available verified and generic cancellation playbooks."""
    orchestrator = CancellationOrchestrator(db)
    return orchestrator.get_playbooks()


@router.get("/eligibility/{commitment_id}", response_model=CancellationEligibilityResponse)
def get_cancellation_eligibility(
    commitment_id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationEligibilityResponse:
    """Analyze commitment and provide detected payment mechanism and recommended playbook."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        return orchestrator.check_eligibility(commitment_id, target_user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=CancellationCaseResponse, status_code=status.HTTP_201_CREATED)
def create_cancellation_case(
    payload: CancellationCaseCreate,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Initiate or retrieve an active cancellation case for a commitment."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.create_or_get_case(
            user_id=target_user_id,
            commitment_id=payload.commitment_id,
            payment_mechanism=payload.payment_mechanism,
            playbook_key=payload.playbook_key,
            user_notes=payload.user_notes,
        )
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("", response_model=List[CancellationCaseResponse])
def list_cancellation_cases(
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> List[CancellationCaseResponse]:
    """List all cancellation cases for the authenticated user/workspace."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    cases = orchestrator.list_cases(target_user_id)
    return [orchestrator.build_case_response(c) for c in cases]


@router.get("/{id}", response_model=CancellationCaseResponse)
def get_cancellation_case(
    id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Get details and step checklist for a specific cancellation case."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    case = orchestrator.get_case(id, target_user_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cancellation case not found.")
    return orchestrator.build_case_response(case)


@router.patch("/{id}", response_model=CancellationCaseResponse)
def update_cancellation_case(
    id: uuid.UUID,
    payload: CancellationCaseUpdate,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Update notes or user references on a cancellation case."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    case = orchestrator.get_case(id, target_user_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cancellation case not found.")

    if payload.user_notes is not None:
        case.user_notes = payload.user_notes
    if payload.evidence_references is not None:
        case.evidence_references = payload.evidence_references
    if payload.status is not None:
        case.status = payload.status.value

    db.commit()
    db.refresh(case)
    return orchestrator.build_case_response(case)


@router.post("/{id}/start", response_model=CancellationCaseResponse)
def start_cancellation_case(
    id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Transition case into IN_PROGRESS state."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.start_case(id, target_user_id)
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/complete-step", response_model=CancellationCaseResponse)
def complete_cancellation_step(
    id: uuid.UUID,
    payload: CancellationStepCompleteRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Record completion of a guidance checklist step."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.complete_step(id, target_user_id, payload.step_id)
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/report-cancelled", response_model=CancellationCaseResponse)
def report_cancellation_outcome(
    id: uuid.UUID,
    payload: CancellationReportRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Record that the user reported cancelling the commitment. Links to Phase 6 cancellation event."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.report_cancelled(
            case_id=id,
            user_id=target_user_id,
            cancellation_date=payload.cancellation_date,
            evidence_references=payload.evidence_references,
            user_notes=payload.user_notes,
        )
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/submit-evidence", response_model=CancellationCaseResponse)
def submit_cancellation_evidence(
    id: uuid.UUID,
    payload: CancellationEvidenceSubmitRequest,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Submit proof/screenshot/ticket reference of cancellation."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.submit_evidence(
            case_id=id,
            user_id=target_user_id,
            evidence_text=payload.evidence_text,
            evidence_url_or_ref=payload.evidence_url_or_ref,
        )
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/verify", response_model=CancellationCaseResponse)
def verify_cancellation(
    id: uuid.UUID,
    verification_notes: str = Query(..., description="Objective verification explanation"),
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Verify cancellation after observing provider confirmation or statement evidence."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.verify_case(id, target_user_id, verification_notes)
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/close", response_model=CancellationCaseResponse)
def close_cancellation_case(
    id: uuid.UUID,
    user_id: Optional[uuid.UUID] = Query(None, description="Optional workspace user UUID"),
    db: Session = Depends(get_db),
) -> CancellationCaseResponse:
    """Close a cancellation case."""
    target_user_id = _resolve_user_id(db, user_id)
    orchestrator = CancellationOrchestrator(db)
    try:
        case = orchestrator.close_case(id, target_user_id)
        return orchestrator.build_case_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
