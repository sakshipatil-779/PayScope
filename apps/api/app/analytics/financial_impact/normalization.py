"""Cadence normalization formulas for monthly and annualized recurring commitment costs."""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple


def round_currency(val: Decimal) -> Decimal:
    """Round a Decimal amount to 2 decimal places using standard financial half-up."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_normalized_costs(
    amount: Decimal,
    cadence: str,
    historical_amounts: Optional[List[Decimal]] = None,
) -> Tuple[Decimal, Decimal, str]:
    """Calculate normalized monthly cost, annualized cost, and an explainable method string.

    Args:
        amount: Representative transaction amount.
        cadence: Cadence string (weekly, fortnightly, monthly, quarterly, annual, variable_monthly, irregular).
        historical_amounts: Optional list of successful historical transaction amounts for variable streams.

    Returns:
        Tuple of (monthly_cost, annual_cost, calculation_method)
    """
    cadence_lower = (cadence or "unknown").lower().strip()
    amt = Decimal(str(amount)) if amount is not None else Decimal("0.00")

    if cadence_lower == "weekly":
        monthly = round_currency((amt * Decimal("52")) / Decimal("12"))
        annual = round_currency(amt * Decimal("52"))
        method = f"Weekly: ₹{amt:,.2f} × 52 / 12 = ₹{monthly:,.2f}/mo (₹{annual:,.2f}/yr)"
        return monthly, annual, method

    elif cadence_lower == "fortnightly":
        monthly = round_currency((amt * Decimal("26")) / Decimal("12"))
        annual = round_currency(amt * Decimal("26"))
        method = f"Fortnightly: ₹{amt:,.2f} × 26 / 12 = ₹{monthly:,.2f}/mo (₹{annual:,.2f}/yr)"
        return monthly, annual, method

    elif cadence_lower == "monthly":
        monthly = round_currency(amt)
        annual = round_currency(amt * Decimal("12"))
        method = f"Monthly: ₹{amt:,.2f} × 12 = ₹{annual:,.2f}/yr"
        return monthly, annual, method

    elif cadence_lower == "quarterly":
        monthly = round_currency(amt / Decimal("3"))
        annual = round_currency(amt * Decimal("4"))
        method = f"Quarterly: ₹{amt:,.2f} / 3 = ₹{monthly:,.2f}/mo (₹{amt:,.2f} × 4 = ₹{annual:,.2f}/yr)"
        return monthly, annual, method

    elif cadence_lower == "annual":
        monthly = round_currency(amt / Decimal("12"))
        annual = round_currency(amt)
        method = f"Annual: ₹{amt:,.2f} / 12 = ₹{monthly:,.2f}/mo (₹{annual:,.2f}/yr)"
        return monthly, annual, method

    elif cadence_lower == "variable_monthly":
        if historical_amounts and len(historical_amounts) > 0:
            sorted_amts = sorted([Decimal(str(a)) for a in historical_amounts])
            n = len(sorted_amts)
            if n % 2 == 1:
                rep = sorted_amts[n // 2]
            else:
                rep = (sorted_amts[n // 2 - 1] + sorted_amts[n // 2]) / Decimal("2")
            monthly = round_currency(rep)
            annual = round_currency(monthly * Decimal("12"))
            method = f"Variable Monthly: Historical median ₹{monthly:,.2f} × 12 = ₹{annual:,.2f}/yr"
            return monthly, annual, method
        else:
            monthly = round_currency(amt)
            annual = round_currency(amt * Decimal("12"))
            method = f"Variable Monthly: Representative ₹{monthly:,.2f} × 12 = ₹{annual:,.2f}/yr"
            return monthly, annual, method

    else:
        # Irregular or unknown cadence - not confirmed recurring
        return Decimal("0.00"), Decimal("0.00"), f"Irregular cadence ({cadence}) - excluded from confirmed recurring"

