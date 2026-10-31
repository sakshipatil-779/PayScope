"""Transaction reprocessing service for merchant intelligence."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.matching.config import DEFAULT_MATCHING_CONFIG
from app.matching.resolver import MerchantResolver
from app.matching.review_service import ReviewService
from app.models.transaction import Transaction


class TransactionReprocessor:
    """Reprocesses stored transactions through the merchant intelligence engine."""

    @classmethod
    def reprocess(
        cls,
        db: Session,
        user_id: uuid.UUID,
        force_all: bool = False,
    ) -> Dict[str, Any]:
        """Idempotently reprocess transactions for a user without overwriting user confirmations."""
        # 1. Fetch transactions for user
        stmt = select(Transaction).where(Transaction.user_id == user_id)
        transactions = list(db.scalars(stmt).all())

        # 2. Instantiate resolver from DB
        resolver = MerchantResolver.from_db(db)

        examined_count = len(transactions)
        matched_count = 0
        review_required_count = 0
        unresolved_count = 0
        skipped_user_confirmed_count = 0

        now = datetime.now(timezone.utc)

        for txn in transactions:
            # Strict safety: never overwrite user-confirmed decisions
            if txn.merchant_match_status == "user_confirmed":
                skipped_user_confirmed_count += 1
                continue

            if not force_all and txn.merchant_match_status == "matched":
                # Already matched and not forcing all
                matched_count += 1
                continue

            resolution = resolver.resolve(txn.raw_descriptor)
            txn.normalised_descriptor = resolution.normalised_descriptor
            txn.matcher_version = DEFAULT_MATCHING_CONFIG.matcher_version
            txn.matched_at = now

            if resolution.status in ("MATCHED_HIGH", "MATCHED_MEDIUM"):
                txn.merchant_id = resolution.merchant_id
                txn.merchant_match_status = "matched"
                txn.merchant_match_method = resolution.match_method
                txn.merchant_match_score = Decimal(str(round(resolution.score, 2)))
                txn.merchant_match_confidence = resolution.confidence_band
                txn.merchant_match_reason = resolution.explanation
                txn.matched_descriptor_alias_id = resolution.matched_alias_id
                matched_count += 1
            elif resolution.status == "NEEDS_REVIEW":
                txn.merchant_id = resolution.merchant_id  # Tentative suggested merchant
                txn.merchant_match_status = "needs_review"
                txn.merchant_match_method = resolution.match_method
                txn.merchant_match_score = Decimal(str(round(resolution.score, 2)))
                txn.merchant_match_confidence = resolution.confidence_band
                txn.merchant_match_reason = resolution.explanation
                txn.matched_descriptor_alias_id = resolution.matched_alias_id
                review_required_count += 1
                # Queue for manual review
                ReviewService.queue_for_review(db, user_id, txn, resolution)
            else:  # UNRESOLVED
                txn.merchant_id = None
                txn.merchant_match_status = "unmatched"
                txn.merchant_match_method = "unresolved"
                txn.merchant_match_score = Decimal("0.00")
                txn.merchant_match_confidence = "none"
                txn.merchant_match_reason = resolution.explanation
                txn.matched_descriptor_alias_id = None
                unresolved_count += 1
                ReviewService.queue_for_review(db, user_id, txn, resolution)

        db.commit()

        return {
            "success": True,
            "examined_count": examined_count,
            "matched_count": matched_count,
            "review_required_count": review_required_count,
            "unresolved_count": unresolved_count,
            "skipped_user_confirmed_count": skipped_user_confirmed_count,
        }
