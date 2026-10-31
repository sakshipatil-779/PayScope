"""Main recurring payment intelligence and cadence discovery orchestrator."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.analytics.amount_analyzer import analyze_amounts
from app.analytics.cadence_classifier import classify_cadence
from app.analytics.commitment_classifier import classify_commitment_type
from app.analytics.commitment_sync import sync_commitment_to_db
from app.analytics.confidence import calculate_confidence
from app.analytics.interval_analyzer import analyze_intervals
from app.analytics.transaction_filter import filter_eligible_transactions
from app.analytics.transaction_grouper import group_transactions_by_stream
from app.models.audit_event import AuditEvent
from app.models.commitment import Commitment
from app.models.transaction import Transaction


@dataclass
class DiscoveryResult:
    """Summary of recurring commitment discovery execution."""
    total_discovered: int = 0
    active_count: int = 0
    candidate_count: int = 0
    needs_review_count: int = 0
    commitments: List[Commitment] = field(default_factory=list)


class CommitmentDetector:
    """Recurring payment cadence and commitment discovery service."""

    def __init__(self, db: Session):
        self.db = db

    def discover_user_commitments(self, user_id: uuid.UUID) -> DiscoveryResult:
        """Run cadence discovery and commitment identification for a workspace user.
        
        Args:
            user_id: The UUID of the workspace user.
            
        Returns:
            DiscoveryResult containing summary counts and persisted commitments.
        """
        # Step 1: Query all transactions for user with eager merchant loading
        txns_stmt = (
            select(Transaction)
            .options(joinedload(Transaction.merchant))
            .where(Transaction.user_id == user_id)
        )
        raw_txns = list(self.db.execute(txns_stmt).scalars().all())

        # Step 2: Filter eligible transactions (debits only, successful, amount > 0)
        eligible_txns = filter_eligible_transactions(raw_txns)
        if not eligible_txns:
            return DiscoveryResult()

        # Step 3: Group transactions into payee candidate streams
        streams = group_transactions_by_stream(user_id, eligible_txns)

        discovered_commitments: List[Commitment] = []
        active_cnt = 0
        candidate_cnt = 0
        review_cnt = 0

        # Step 4: Analyze each stream
        for stream in streams:
            dates = []
            for t in stream.transactions:
                if isinstance(t.transaction_date, str):
                    dates.append(datetime.fromisoformat(t.transaction_date).date())
                elif isinstance(t.transaction_date, datetime):
                    dates.append(t.transaction_date.date())
                else:
                    dates.append(t.transaction_date)
            amounts = [t.amount for t in stream.transactions]

            interval_info = analyze_intervals(dates)
            amount_info = analyze_amounts(amounts)

            cadence_res = classify_cadence(
                interval_info=interval_info,
                amount_info=amount_info,
                merchant_category=stream.merchant_category,
                display_name=stream.display_name,
            )

            # Skip streams that do not qualify as recurring or candidates
            if not cadence_res.is_recurring and not cadence_res.is_candidate_only:
                continue

            # Check merchant resolution
            first_txn = stream.transactions[0]
            merchant_obj = first_txn.merchant if stream.merchant_id is not None else None
            is_resolved = (
                stream.merchant_id is not None
                and first_txn.merchant_match_status not in ("unmatched", "needs_review")
            )

            commitment_type = classify_commitment_type(
                merchant=merchant_obj,
                display_name=stream.display_name,
                is_merchant_resolved=is_resolved,
            )

            confidence_eval = calculate_confidence(
                cadence_res=cadence_res,
                interval_info=interval_info,
                amount_info=amount_info,
                merchant_match_confidence=first_txn.merchant_match_confidence,
                is_merchant_resolved=is_resolved,
                payment_channels=stream.payment_channels,
                display_name=stream.display_name,
            )

            commitment = sync_commitment_to_db(
                db=self.db,
                stream=stream,
                cadence_res=cadence_res,
                interval_info=interval_info,
                amount_info=amount_info,
                confidence_assessment=confidence_eval,
                commitment_type=commitment_type,
            )
            discovered_commitments.append(commitment)

            if commitment.status == "active":
                active_cnt += 1
            elif commitment.status == "candidate":
                candidate_cnt += 1
            elif commitment.status in ("review_required", "needs_review"):
                review_cnt += 1

        # Step 5: Log audit event
        audit = AuditEvent(
            id=uuid.uuid4(),
            user_id=user_id,
            entity_type="commitment",
            entity_id=None,
            action="discover_commitments",
            actor_type="system",
            after_summary={
                "total_discovered": len(discovered_commitments),
                "active_count": active_cnt,
                "candidate_count": candidate_cnt,
                "needs_review_count": review_cnt,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(audit)
        self.db.commit()

        return DiscoveryResult(
            total_discovered=len(discovered_commitments),
            active_count=active_cnt,
            candidate_count=candidate_cnt,
            needs_review_count=review_cnt,
            commitments=discovered_commitments,
        )
