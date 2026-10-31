"""Canonical merchant financial impact ranking and alias aggregation."""
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.analytics.financial_impact.commitment_costs import get_user_commitment_costs
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.schemas import MerchantCostRanking
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant
from app.models.transaction import Transaction


def get_user_merchant_analysis(
    db: Session,
    user_id: uuid.UUID,
) -> List[MerchantCostRanking]:
    """Rank canonical merchants by confirmed recurring expenditure and aggregate all descriptor aliases."""
    cost_items = get_user_commitment_costs(db, user_id)
    confirmed_items = [item for item in cost_items if item.is_confirmed]

    total_recurring_annual = sum((item.annualized_cost for item in confirmed_items), Decimal("0.00"))

    # Group commitments by canonical merchant_id (or None for unresolved)
    merchant_groups: Dict[Optional[uuid.UUID], Dict[str, Any]] = {}

    for item in confirmed_items:
        m_id = item.merchant_id
        if m_id not in merchant_groups:
            merchant_groups[m_id] = {
                "name": item.merchant_name,
                "category": item.commitment_type,
                "monthly": Decimal("0.00"),
                "annual": Decimal("0.00"),
                "count": 0,
                "commitment_ids": [],
            }
        merchant_groups[m_id]["monthly"] += item.normalized_monthly_cost
        merchant_groups[m_id]["annual"] += item.annualized_cost
        merchant_groups[m_id]["count"] += 1
        merchant_groups[m_id]["commitment_ids"].append(item.commitment_id)

    # Fetch aliases for known merchants
    known_m_ids = [m_id for m_id in merchant_groups.keys() if m_id is not None]
    alias_map: Dict[uuid.UUID, List[str]] = {}
    if known_m_ids:
        aliases_stmt = select(DescriptorAlias).where(DescriptorAlias.merchant_id.in_(known_m_ids))
        aliases = db.scalars(aliases_stmt).all()
        for a in aliases:
            alias_map.setdefault(a.merchant_id, []).append(a.pattern)

    result: List[MerchantCostRanking] = []
    for m_id, grp in merchant_groups.items():
        c_ids = grp["commitment_ids"]
        hist_12m = Decimal("0.00")
        if c_ids:
            hist_stmt = (
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0.00")))
                .join(CommitmentTransaction, CommitmentTransaction.transaction_id == Transaction.id)
                .where(
                    Transaction.user_id == user_id,
                    Transaction.direction.ilike("debit"),
                    Transaction.transaction_status.ilike("successful"),
                    CommitmentTransaction.commitment_id.in_(c_ids),
                )
            )
            hist_12m = db.scalar(hist_stmt) or Decimal("0.00")

        pct = (
            round_currency((grp["annual"] / total_recurring_annual) * Decimal("100.0"))
            if total_recurring_annual > Decimal("0.00")
            else Decimal("0.00")
        )

        aliases = alias_map.get(m_id, []) if m_id else []

        result.append(
            MerchantCostRanking(
                merchant_id=m_id,
                merchant_name=grp["name"] or "Unresolved Merchant",
                category=grp["category"],
                monthly_cost=round_currency(grp["monthly"]),
                annualized_cost=round_currency(grp["annual"]),
                historical_spend_12m=round_currency(hist_12m),
                percentage_of_total=pct,
                commitment_count=grp["count"],
                aliases=aliases,
            )
        )

    result.sort(key=lambda x: x.annualized_cost, reverse=True)
    return result

