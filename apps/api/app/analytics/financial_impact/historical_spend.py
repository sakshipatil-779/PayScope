"""Historical expenditure analysis across selectable time horizons and monthly spend timeline."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.analytics.financial_impact.config import HISTORICAL_PERIODS
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.schemas import (
    HistoricalPeriodSpend,
    HistoricalSpendResponse,
    MonthlyTrendPoint,
)
from app.models.commitment_transaction import CommitmentTransaction
from app.models.transaction import Transaction


def get_user_historical_spend(
    db: Session,
    user_id: uuid.UUID,
    as_of: Optional[datetime] = None,
) -> HistoricalSpendResponse:
    """Calculate historical expenditure across 30d, 90d, 180d, 365d, and all history.

    Safeguards:
    - Filters ONLY successful debits for gross debit spend.
    - Explicitly excludes failed, reversed, and pending transactions.
    - Excludes duplicate transaction records.
    - Tracks credits and net spend separately.
    """
    now = as_of or datetime.now(timezone.utc)

    # Fetch all transactions for this user
    all_txs_stmt = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.transaction_date.desc())
    )
    all_txs = db.scalars(all_txs_stmt).all()

    # Pre-fetch transaction IDs that belong to confirmed recurring commitments
    recurring_tx_ids_stmt = (
        select(CommitmentTransaction.transaction_id)
        .join(Transaction, CommitmentTransaction.transaction_id == Transaction.id)
        .where(Transaction.user_id == user_id)
    )
    recurring_tx_ids: Set[uuid.UUID] = set(db.scalars(recurring_tx_ids_stmt).all())

    # De-duplicate transactions if needed
    seen_external_ids: Set[str] = set()
    deduped_txs: List[Transaction] = []
    excluded_duplicates_count = 0

    for tx in all_txs:
        ext_id = tx.external_synthetic_id
        if ext_id:
            if ext_id in seen_external_ids:
                excluded_duplicates_count += 1
                continue
            seen_external_ids.add(ext_id)
        deduped_txs.append(tx)

    # Helper for period window filtering
    def _evaluate_period(period_key: str, days: Optional[int], label: str) -> HistoricalPeriodSpend:
        start_threshold = now - timedelta(days=days) if days is not None else None
        
        gross_debit = Decimal("0.00")
        credits = Decimal("0.00")
        valid_count = 0
        failed_count = 0
        period_dups = 0

        for tx in all_txs:
            # Check date window
            tx_dt = tx.transaction_date
            if tx_dt.tzinfo is None:
                tx_dt = tx_dt.replace(tzinfo=timezone.utc)
            if start_threshold and tx_dt < start_threshold:
                continue

            # Check status
            st = (tx.transaction_status or "").lower()
            dir_ = (tx.direction or "").lower()

            if st in ("failed", "reversed", "pending"):
                failed_count += 1
                continue

            # Duplicate check
            ext_id = tx.external_synthetic_id
            # If it was excluded in deduped list
            if tx not in deduped_txs:
                period_dups += 1
                continue

            amt = tx.amount or Decimal("0.00")
            if dir_ == "debit":
                gross_debit += amt
                valid_count += 1
            elif dir_ == "credit":
                credits += amt

        net_spend = gross_debit - credits

        return HistoricalPeriodSpend(
            period=period_key,
            period_label=label,
            start_date=start_threshold,
            end_date=now,
            gross_debit_amount=round_currency(gross_debit),
            total_credits=round_currency(credits),
            net_spend=round_currency(net_spend),
            transaction_count=valid_count,
            excluded_duplicates_count=period_dups,
            excluded_failed_count=failed_count,
        )

    period_specs = [
        ("30d", 30, "Last 30 Days"),
        ("90d", 90, "Last 90 Days"),
        ("180d", 180, "Last 6 Months"),
        ("365d", 365, "Last 12 Months"),
        ("all", None, "All Time History"),
    ]

    periods_summary = [
        _evaluate_period(key, days, label)
        for key, days, label in period_specs
    ]

    # Build monthly timeline
    monthly_data: Dict[str, Dict[str, Decimal]] = {}
    for tx in deduped_txs:
        st = (tx.transaction_status or "").lower()
        if st != "successful":
            continue

        tx_dt = tx.transaction_date
        m_key = tx_dt.strftime("%Y-%m")
        if m_key not in monthly_data:
            monthly_data[m_key] = {
                "gross_debit": Decimal("0.00"),
                "credits": Decimal("0.00"),
                "recurring_debit": Decimal("0.00"),
            }

        amt = tx.amount or Decimal("0.00")
        dir_ = (tx.direction or "").lower()

        if dir_ == "debit":
            monthly_data[m_key]["gross_debit"] += amt
            if tx.id in recurring_tx_ids:
                monthly_data[m_key]["recurring_debit"] += amt
        elif dir_ == "credit":
            monthly_data[m_key]["credits"] += amt

    sorted_months = sorted(monthly_data.keys())
    monthly_timeline: List[MonthlyTrendPoint] = []
    for m in sorted_months:
        d = monthly_data[m]
        gross = d["gross_debit"]
        cred = d["credits"]
        rec = d["recurring_debit"]
        net = gross - cred
        
        # Label e.g. "Sep 2026"
        dt_obj = datetime.strptime(m, "%Y-%m")
        label = dt_obj.strftime("%b %Y")

        monthly_timeline.append(
            MonthlyTrendPoint(
                month_key=m,
                month_label=label,
                gross_debit=round_currency(gross),
                credits=round_currency(cred),
                net_spend=round_currency(net),
                recurring_debit=round_currency(rec),
            )
        )

    return HistoricalSpendResponse(
        currency="INR",
        periods=periods_summary,
        monthly_timeline=monthly_timeline,
    )

