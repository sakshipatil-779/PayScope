"""Upcoming expected recurring commitment expenditures."""
import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.analytics.financial_impact.commitment_costs import get_user_commitment_costs
from app.analytics.financial_impact.normalization import round_currency
from app.analytics.financial_impact.schemas import (
    UpcomingExpenseItem,
    UpcomingExpenditureResponse,
)


def get_user_upcoming_expenditure(
    db: Session,
    user_id: uuid.UUID,
    as_of: Optional[date] = None,
) -> UpcomingExpenditureResponse:
    """Project expected commitment debits for next 30 and 60 days based on verified cadence.

    Distinguishes scheduled vs estimated dates, and excludes unconfirmed one-off transactions.
    """
    today = as_of or date.today()
    cutoff_30d = today + timedelta(days=30)
    cutoff_60d = today + timedelta(days=60)

    cost_items = get_user_commitment_costs(db, user_id)
    # Consider active/confirmed commitments or commitments with explicit next_expected_date
    candidates = [
        item for item in cost_items
        if item.is_confirmed and item.representative_amount > Decimal("0.00")
    ]

    items: List[UpcomingExpenseItem] = []
    total_30d = Decimal("0.00")
    total_60d = Decimal("0.00")

    for item in candidates:
        exp_date = item.next_expected_date
        basis = "scheduled"

        # If next_expected_date is missing or in the past, synthesize realistic next date using cadence
        if not exp_date or exp_date < today:
            basis = "estimated_cadence"
            cad = (item.cadence or "monthly").lower()
            if cad == "weekly":
                exp_date = today + timedelta(days=7)
            elif cad == "fortnightly":
                exp_date = today + timedelta(days=14)
            elif cad == "quarterly":
                exp_date = today + timedelta(days=45)
            elif cad == "annual":
                exp_date = today + timedelta(days=60)
            else:  # monthly / variable_monthly
                exp_date = today + timedelta(days=15)

        # Check if within 60 days
        if today <= exp_date <= cutoff_60d:
            amt = item.representative_amount
            if exp_date <= cutoff_30d:
                total_30d += amt
            total_60d += amt

            items.append(
                UpcomingExpenseItem(
                    commitment_id=item.commitment_id,
                    display_name=item.display_name,
                    merchant_name=item.merchant_name,
                    expected_date=exp_date,
                    estimated_amount=round_currency(amt),
                    currency=item.currency,
                    cadence=item.cadence,
                    estimation_basis=basis,
                    is_confirmed=item.is_confirmed,
                )
            )

    items.sort(key=lambda x: x.expected_date)

    return UpcomingExpenditureResponse(
        currency="INR",
        total_upcoming_30d=round_currency(total_30d),
        total_upcoming_60d=round_currency(total_60d),
        items=items,
    )

