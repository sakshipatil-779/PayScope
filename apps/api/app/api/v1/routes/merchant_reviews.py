"""Manual review queue endpoints for merchant intelligence."""
import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.matching.review_service import ReviewService
from app.matching.schemas import CorrectReviewRequest, ManualReviewItemResponse
from app.models.manual_review_item import ManualReviewItem
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/merchant-reviews", tags=["Merchant Reviews"])


@router.get("", response_model=List[ManualReviewItemResponse], status_code=status.HTTP_200_OK)
def list_merchant_reviews(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: open, accepted, corrected, dismissed"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve queued manual review items for the current demo user."""
    user = UserRepository.get_or_create_demo_user(db)
    items = ReviewService.list_reviews(db, user_id=user.id, status=status_filter, limit=limit, offset=offset)

    results = []
    for it in items:
        candidates = it.candidate_payload.get("candidates") if it.candidate_payload else None
        sug_name = it.suggested_merchant.canonical_name if it.suggested_merchant else None
        results.append(
            ManualReviewItemResponse(
                id=it.id,
                user_id=it.user_id,
                transaction_id=it.transaction_id,
                item_type=it.item_type,
                raw_descriptor=it.raw_descriptor,
                normalised_descriptor=it.normalised_descriptor,
                suggested_merchant_id=it.suggested_merchant_id,
                suggested_merchant_name=sug_name,
                similarity_score=float(it.similarity_score) if it.similarity_score is not None else None,
                confidence_band=it.confidence_band,
                match_method=it.match_method,
                explanation=it.explanation,
                reason_code=it.reason_code,
                status=it.status,
                candidates=candidates,
                user_selected_merchant_id=it.user_selected_merchant_id,
                decision_notes=it.decision_notes,
                created_at=it.created_at,
                reviewed_at=it.reviewed_at,
            )
        )
    return results


@router.get("/{review_id}", response_model=ManualReviewItemResponse, status_code=status.HTTP_200_OK)
def get_merchant_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """Retrieve a single manual review item with full candidate breakdown."""
    item = db.scalar(select(ManualReviewItem).where(ManualReviewItem.id == review_id))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review item not found.")

    candidates = item.candidate_payload.get("candidates") if item.candidate_payload else None
    sug_name = item.suggested_merchant.canonical_name if item.suggested_merchant else None

    return ManualReviewItemResponse(
        id=item.id,
        user_id=item.user_id,
        transaction_id=item.transaction_id,
        item_type=item.item_type,
        raw_descriptor=item.raw_descriptor,
        normalised_descriptor=item.normalised_descriptor,
        suggested_merchant_id=item.suggested_merchant_id,
        suggested_merchant_name=sug_name,
        similarity_score=float(item.similarity_score) if item.similarity_score is not None else None,
        confidence_band=item.confidence_band,
        match_method=item.match_method,
        explanation=item.explanation,
        reason_code=item.reason_code,
        status=item.status,
        candidates=candidates,
        user_selected_merchant_id=item.user_selected_merchant_id,
        decision_notes=item.decision_notes,
        created_at=item.created_at,
        reviewed_at=item.reviewed_at,
    )


@router.post("/{review_id}/accept", status_code=status.HTTP_200_OK)
def accept_merchant_review(
    review_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """User confirms and accepts the suggested merchant match."""
    try:
        item = ReviewService.accept_match(db, review_id=review_id)
        return {
            "success": True,
            "review_id": str(item.id),
            "status": item.status,
            "merchant_id": str(item.suggested_merchant_id),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{review_id}/correct", status_code=status.HTTP_200_OK)
def correct_merchant_review(
    review_id: uuid.UUID,
    req: CorrectReviewRequest,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """User selects a different merchant and optionally creates a new descriptor alias."""
    try:
        item = ReviewService.correct_match(
            db=db,
            review_id=review_id,
            selected_merchant_id=req.merchant_id,
            create_alias=req.create_alias,
            decision_notes=req.decision_notes,
        )
        return {
            "success": True,
            "review_id": str(item.id),
            "status": item.status,
            "selected_merchant_id": str(item.user_selected_merchant_id),
            "alias_created": req.create_alias,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{review_id}/dismiss", status_code=status.HTTP_200_OK)
def dismiss_merchant_review(
    review_id: uuid.UUID,
    notes: Optional[str] = Query(None, description="Optional dismissal notes"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """User marks descriptor as unknown or dismisses review."""
    try:
        item = ReviewService.dismiss_match(db, review_id=review_id, decision_notes=notes)
        return {
            "success": True,
            "review_id": str(item.id),
            "status": item.status,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
