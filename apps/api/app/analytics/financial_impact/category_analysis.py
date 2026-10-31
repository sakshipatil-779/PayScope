"""Category-level financial impact and recurring expenditure distribution."""
import uuid
from decimal import Decimal
from typing import Any, Dict, List
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.financial_impact.commitment_costs import get_user_commitment_costs
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.schemas import CategoryCostBreakdown
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.transaction import Transaction


CATEGORY_LABELS = {
    "entertainment": "Entertainment & Streaming",
    "productivity": "Productivity & SaaS",
    "fitness": "Fitness & Health",
    "utilities": "Utilities & Telecom",
    "insurance": "Insurance & Protection",
    "finance": "Finance & EMI",
    "cloud": "Cloud Infrastructure & Dev",
    "other": "Other Subscriptions",
}


def normalize_category_name(raw_type: str, merchant_cat: str = "") -> str:
    """Map commitment type or merchant category to a standard financial category."""
    combined = f"{raw_type} {merchant_cat}".lower()

    if any(k in combined for k in ("stream", "entertainment", "ott", "music", "media", "gaming", "hotstar", "netflix", "spotify")):
        return "entertainment"
    if any(k in combined for k in ("cloud", "aws", "gcp", "azure", "server", "hosting")):
        return "cloud"
    if any(k in combined for k in ("productiv", "saas", "software", "workspace", "tools", "clouddesk")):
        return "productivity"
    if any(k in combined for k in ("fit", "gym", "health", "cult", "wellness")):
        return "fitness"
    if any(k in combined for k in ("utilit", "telecom", "broadband", "mobile", "electric", "bill", "airtel", "bescom")):
        return "utilities"
    if any(k in combined for k in ("insur", "suraksha", "lic", "policy", "premium")):
        return "insurance"
    if any(k in combined for k in ("loan", "emi", "finance", "credit", "bank")):
        return "finance"
    return "other"


def get_user_category_analysis(
    db: Session,
    user_id: uuid.UUID,
) -> List[CategoryCostBreakdown]:
    """Calculate category cost breakdowns for confirmed commitments and linked historical spend."""
    cost_items = get_user_commitment_costs(db, user_id)
    confirmed_items = [item for item in cost_items if item.is_confirmed]

    total_recurring_monthly = sum((item.normalized_monthly_cost for item in confirmed_items), Decimal("0.00"))
    total_recurring_annual = sum((item.annualized_cost for item in confirmed_items), Decimal("0.00"))

    # Map each commitment to a normalized category
    category_buckets: Dict[str, Dict[str, Any]] = {}
    for item in confirmed_items:
        cat_key = normalize_category_name(item.commitment_type)
        if cat_key not in category_buckets:
            category_buckets[cat_key] = {
                "monthly": Decimal("0.00"),
                "annual": Decimal("0.00"),
                "count": 0,
                "commitment_ids": [],
            }
        category_buckets[cat_key]["monthly"] += item.normalized_monthly_cost
        category_buckets[cat_key]["annual"] += item.annualized_cost
        category_buckets[cat_key]["count"] += 1
        category_buckets[cat_key]["commitment_ids"].append(item.commitment_id)

    # Query historical 12m spend for transactions linked to commitments in each category
    result: List[CategoryCostBreakdown] = []

    for cat_key, b in category_buckets.items():
        c_ids = b["commitment_ids"]
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
            round_currency((b["annual"] / total_recurring_annual) * Decimal("100.0"))
            if total_recurring_annual > Decimal("0.00")
            else Decimal("0.00")
        )

        label = CATEGORY_LABELS.get(cat_key, cat_key.title())

        result.append(
            CategoryCostBreakdown(
                category=cat_key,
                category_label=label,
                monthly_cost=round_currency(b["monthly"]),
                annualized_cost=round_currency(b["annual"]),
                historical_spend_12m=round_currency(hist_12m),
                percentage_of_recurring=pct,
                commitment_count=b["count"],
            )
        )

    # Sort descending by annualized cost
    result.sort(key=lambda x: x.annualized_cost, reverse=True)
    return result
