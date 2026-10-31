"""Manual review service handling queue management and user review decisions."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import Session
from app.matching.normalizer import DescriptorNormalizer
from app.matching.schemas import MatchResolutionResult
from app.models.audit_event import AuditEvent
from app.models.descriptor_alias import DescriptorAlias
from app.models.manual_review_item import ManualReviewItem
from app.models.merchant import Merchant
from app.models.transaction import Transaction


class ReviewService:
    """Manages manual review queue, user actions, and audit logging."""

    @classmethod
    def queue_for_review(
        cls,
        db: Session,
        user_id: uuid.UUID,
        transaction: Transaction,
        resolution: MatchResolutionResult,
    ) -> ManualReviewItem:
        """Create or update an existing open review queue item for this descriptor."""
        # Check for existing open review item for this descriptor
        stmt = select(ManualReviewItem).where(
            ManualReviewItem.user_id == user_id,
            ManualReviewItem.raw_descriptor == transaction.raw_descriptor,
            ManualReviewItem.status == "open",
        )
        existing_item = db.scalar(stmt)

        candidate_dicts = [
            {
                "merchant_id": str(c.merchant_id),
                "canonical_name": c.canonical_name,
                "category": c.category,
                "score": c.score,
                "method": c.method,
                "confidence_band": c.confidence_band,
            }
            for c in resolution.candidates
        ]

        if existing_item:
            # Update candidate payload and linked transaction
            existing_item.transaction_id = transaction.id
            existing_item.suggested_merchant_id = resolution.merchant_id
            existing_item.candidate_payload = {"candidates": candidate_dicts}
            existing_item.similarity_score = Decimal(str(round(resolution.score, 2)))
            existing_item.confidence_band = resolution.confidence_band
            existing_item.match_method = resolution.match_method
            existing_item.explanation = resolution.explanation
            existing_item.reason_code = "ambiguous_match" if resolution.is_ambiguous else "low_confidence_match"
            return existing_item

        new_item = ManualReviewItem(
            user_id=user_id,
            transaction_id=transaction.id,
            item_type="merchant_match",
            raw_descriptor=transaction.raw_descriptor,
            normalised_descriptor=resolution.normalised_descriptor,
            suggested_merchant_id=resolution.merchant_id,
            candidate_payload={"candidates": candidate_dicts},
            similarity_score=Decimal(str(round(resolution.score, 2))),
            confidence_band=resolution.confidence_band,
            match_method=resolution.match_method,
            explanation=resolution.explanation,
            reason_code="ambiguous_match" if resolution.is_ambiguous else "low_confidence_match",
            status="open",
        )
        db.add(new_item)
        return new_item

    @classmethod
    def accept_match(
        cls,
        db: Session,
        review_id: uuid.UUID,
        reviewed_by: Optional[str] = "demo_user",
    ) -> ManualReviewItem:
        """User confirms the suggested merchant candidate."""
        item = db.scalar(select(ManualReviewItem).where(ManualReviewItem.id == review_id))
        if not item:
            raise ValueError(f"Review item {review_id} not found.")

        if not item.suggested_merchant_id:
            raise ValueError("No suggested merchant to accept.")

        now = datetime.now(timezone.utc)
        item.status = "accepted"
        item.reviewed_by = reviewed_by
        item.reviewed_at = now
        item.user_selected_merchant_id = item.suggested_merchant_id

        # Update linked transaction
        if item.transaction_id:
            txn = db.scalar(select(Transaction).where(Transaction.id == item.transaction_id))
            if txn:
                txn.merchant_id = item.suggested_merchant_id
                txn.merchant_match_status = "user_confirmed"
                txn.merchant_match_method = "user_confirmed"
                txn.merchant_match_confidence = "high"
                txn.matched_at = now

        # Create audit event
        audit = AuditEvent(
            user_id=item.user_id,
            entity_type="merchant_match",
            entity_id=item.id,
            action="manual_review_accepted",
            actor_type="user",
            after_summary={
                "merchant_id": str(item.suggested_merchant_id),
                "raw_descriptor": item.raw_descriptor,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def correct_match(
        cls,
        db: Session,
        review_id: uuid.UUID,
        selected_merchant_id: uuid.UUID,
        create_alias: bool = False,
        decision_notes: Optional[str] = None,
        reviewed_by: Optional[str] = "demo_user",
    ) -> ManualReviewItem:
        """User corrects the merchant and optionally adds a new descriptor alias."""
        item = db.scalar(select(ManualReviewItem).where(ManualReviewItem.id == review_id))
        if not item:
            raise ValueError(f"Review item {review_id} not found.")

        merchant = db.scalar(select(Merchant).where(Merchant.id == selected_merchant_id))
        if not merchant:
            raise ValueError(f"Target merchant {selected_merchant_id} not found.")

        now = datetime.now(timezone.utc)
        item.status = "corrected"
        item.reviewed_by = reviewed_by
        item.reviewed_at = now
        item.user_selected_merchant_id = selected_merchant_id
        item.decision_notes = decision_notes

        # Update linked transaction
        alias_id = None
        if create_alias:
            norm_alias = DescriptorNormalizer.normalize(item.raw_descriptor)
            # Check if alias already exists
            existing_alias = db.scalar(
                select(DescriptorAlias).where(
                    DescriptorAlias.merchant_id == selected_merchant_id,
                    DescriptorAlias.normalised_alias == norm_alias,
                )
            )
            if not existing_alias and norm_alias:
                new_alias = DescriptorAlias(
                    merchant_id=selected_merchant_id,
                    alias_text=item.raw_descriptor,
                    normalised_alias=norm_alias,
                    matcher_type="exact",
                    confidence_band="high",
                    reference_source="user_review_correction",
                    is_active=True,
                )
                db.add(new_alias)
                db.flush()
                alias_id = new_alias.id
            elif existing_alias:
                alias_id = existing_alias.id

        if item.transaction_id:
            txn = db.scalar(select(Transaction).where(Transaction.id == item.transaction_id))
            if txn:
                txn.merchant_id = selected_merchant_id
                txn.merchant_match_status = "user_confirmed"
                txn.merchant_match_method = "user_confirmed"
                txn.merchant_match_confidence = "high"
                txn.matched_descriptor_alias_id = alias_id
                txn.matched_at = now

        # Create audit event
        audit = AuditEvent(
            user_id=item.user_id,
            entity_type="merchant_match",
            entity_id=item.id,
            action="manual_review_corrected",
            actor_type="user",
            after_summary={
                "merchant_id": str(selected_merchant_id),
                "created_alias": create_alias,
                "notes": decision_notes,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def dismiss_match(
        cls,
        db: Session,
        review_id: uuid.UUID,
        decision_notes: Optional[str] = None,
        reviewed_by: Optional[str] = "demo_user",
    ) -> ManualReviewItem:
        """User marks descriptor as unknown or dismisses review."""
        item = db.scalar(select(ManualReviewItem).where(ManualReviewItem.id == review_id))
        if not item:
            raise ValueError(f"Review item {review_id} not found.")

        now = datetime.now(timezone.utc)
        item.status = "dismissed"
        item.reviewed_by = reviewed_by
        item.reviewed_at = now
        item.decision_notes = decision_notes

        # Transaction remains unmatched
        if item.transaction_id:
            txn = db.scalar(select(Transaction).where(Transaction.id == item.transaction_id))
            if txn:
                txn.merchant_id = None
                txn.merchant_match_status = "unmatched"
                txn.merchant_match_method = "user_dismissed"
                txn.matched_at = now

        # Create audit event
        audit = AuditEvent(
            user_id=item.user_id,
            entity_type="merchant_match",
            entity_id=item.id,
            action="manual_review_dismissed",
            actor_type="user",
            after_summary={"notes": decision_notes},
        )
        db.add(audit)
        db.commit()
        db.refresh(item)
        return item

    @classmethod
    def list_reviews(
        cls,
        db: Session,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ManualReviewItem]:
        """List review items with optional status filtering."""
        stmt = select(ManualReviewItem).where(ManualReviewItem.user_id == user_id)
        if status:
            stmt = stmt.where(ManualReviewItem.status == status)
        stmt = stmt.order_by(desc(ManualReviewItem.created_at)).limit(limit).offset(offset)
        return list(db.scalars(stmt).all())
