"""Cadence classifier for detecting payment frequency patterns."""
from dataclasses import dataclass
from typing import List, Optional
from app.analytics.amount_analyzer import AmountAnalysis
from app.analytics.config import (
    CadenceIntervalBounds,
    MIN_ANNUAL_EVENTS_FOR_CONFIRMED,
    MIN_IRREGULAR_EVENTS,
    MIN_RECURRING_EVENTS,
)
from app.analytics.interval_analyzer import IntervalAnalysis

bounds = CadenceIntervalBounds()


@dataclass
class CadenceClassification:
    """Result of cadence classification."""
    cadence: str  # weekly, fortnightly, monthly, quarterly, annual, variable_monthly, irregular, unknown
    is_recurring: bool
    is_candidate_only: bool
    primary_reason: str


def classify_cadence(
    interval_info: IntervalAnalysis,
    amount_info: AmountAnalysis,
    merchant_category: Optional[str] = None,
    display_name: str = "",
) -> CadenceClassification:
    """Classify payment cadence based on interval analysis and amount pattern.
    
    Args:
        interval_info: Statistical summary of transaction intervals.
        amount_info: Statistical summary of transaction amounts.
        merchant_category: Optional merchant category (e.g. 'Insurance').
        display_name: Name of payee/merchant for context.
        
    Returns:
        CadenceClassification detailing cadence and recurrence qualification.
    """
    count = interval_info.count

    # Single transaction case
    if count == 1:
        # Check if payee has insurance or annual characteristics
        name_lower = display_name.lower()
        cat_lower = (merchant_category or "").lower()
        is_potential_annual = (
            "insurance" in cat_lower
            or "insurance" in name_lower
            or "annual" in name_lower
            or "premium" in name_lower
            or float(amount_info.representative_amount) >= 5000.0
        )
        if is_potential_annual:
            return CadenceClassification(
                cadence="annual",
                is_recurring=False,  # Single observation is NOT confirmed recurring
                is_candidate_only=True,
                primary_reason="Single transaction observed for potential annual commitment; insufficient evidence for confirmed recurrence.",
            )
        return CadenceClassification(
            cadence="unknown",
            is_recurring=False,
            is_candidate_only=False,
            primary_reason="Single transaction observed; insufficient evidence to establish recurrence.",
        )

    if count < MIN_RECURRING_EVENTS:
        return CadenceClassification(
            cadence="unknown",
            is_recurring=False,
            is_candidate_only=False,
            primary_reason=f"Insufficient transaction count ({count}) for recurrence.",
        )

    med_days = interval_info.median_interval
    month_diffs = interval_info.calendar_month_intervals
    intervals = interval_info.intervals

    # 1. Weekly: median interval 6-8 days
    if bounds.weekly[0] <= med_days <= bounds.weekly[1]:
        all_weekly_like = all(5 <= i <= 10 for i in intervals)
        if all_weekly_like:
            return CadenceClassification(
                cadence="weekly",
                is_recurring=True,
                is_candidate_only=False,
                primary_reason=f"Consistent weekly intervals observed (median {med_days:.1f} days).",
            )

    # 2. Fortnightly: median interval 12-16 days
    if bounds.fortnightly[0] <= med_days <= bounds.fortnightly[1]:
        all_fortnightly_like = all(10 <= i <= 18 for i in intervals)
        if all_fortnightly_like:
            return CadenceClassification(
                cadence="fortnightly",
                is_recurring=True,
                is_candidate_only=False,
                primary_reason=f"Consistent fortnightly intervals observed (median {med_days:.1f} days).",
            )

    # 3. Monthly / Variable Monthly
    # Must have at least 1 calendar month between consecutive charges (no same-month repeats)
    no_same_month_repeats = all(md >= 1 for md in month_diffs)
    is_calendar_monthly = (
        no_same_month_repeats
        and len(month_diffs) > 0
        and (sum(1 for md in month_diffs if md == 1) / len(month_diffs)) >= 0.75
    )
    is_day_interval_monthly = (
        no_same_month_repeats
        and bounds.monthly_days[0] <= med_days <= bounds.monthly_days[1]
    )

    if (is_calendar_monthly or is_day_interval_monthly) and med_days >= 28.0:
        # Differentiate fixed vs variable amount
        if amount_info.amount_pattern == "variable":
            return CadenceClassification(
                cadence="variable_monthly",
                is_recurring=True,
                is_candidate_only=False,
                primary_reason=f"Regular monthly cadence with variable amounts (median {med_days:.1f} days, CV={amount_info.cv:.2f}).",
            )
        else:
            return CadenceClassification(
                cadence="monthly",
                is_recurring=True,
                is_candidate_only=False,
                primary_reason=f"Regular monthly cadence with stable amounts (median {med_days:.1f} days).",
            )

    # 4. Quarterly: ~3 calendar months or 80-100 days
    is_calendar_quarterly = (
        len(month_diffs) > 0
        and (sum(1 for md in month_diffs if md == 3) / len(month_diffs)) >= 0.75
    )
    is_day_quarterly = bounds.quarterly_days[0] <= med_days <= bounds.quarterly_days[1]
    if is_calendar_quarterly or is_day_quarterly:
        return CadenceClassification(
            cadence="quarterly",
            is_recurring=True,
            is_candidate_only=False,
            primary_reason=f"Quarterly cadence observed (median {med_days:.1f} days).",
        )

    # 5. Annual: ~12 calendar months or 350-380 days (requires >= 2 events)
    is_calendar_annual = (
        len(month_diffs) > 0
        and (sum(1 for md in month_diffs if md in (11, 12, 13)) / len(month_diffs)) >= 0.75
    )
    is_day_annual = bounds.annual_days[0] <= med_days <= bounds.annual_days[1]
    if (is_calendar_annual or is_day_annual) and count >= MIN_ANNUAL_EVENTS_FOR_CONFIRMED:
        return CadenceClassification(
            cadence="annual",
            is_recurring=True,
            is_candidate_only=False,
            primary_reason=f"Confirmed annual recurrence across multiple billing cycles ({count} events).",
        )

    # 6. Irregular: >= 4 events, intervals between 18 and 38 days, not calendar monthly
    if (
        count >= MIN_IRREGULAR_EVENTS
        and bounds.irregular_days[0] <= med_days <= bounds.irregular_days[1]
        and all(15 <= i <= 45 for i in intervals)
    ):
        return CadenceClassification(
            cadence="irregular",
            is_recurring=True,
            is_candidate_only=False,
            primary_reason=f"Irregular repeat transactions observed ({count} events, interval range {interval_info.min_interval}-{interval_info.max_interval} days).",
        )

    # Fallback: Does not match any cadence
    return CadenceClassification(
        cadence="unknown",
        is_recurring=False,
        is_candidate_only=False,
        primary_reason=f"Transaction intervals (median {med_days:.1f} days) do not match a recurring cadence.",
    )
