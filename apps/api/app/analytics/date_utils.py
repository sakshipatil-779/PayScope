"""Date utilities for recurrence interval calculations and calendar-aware next-date projection."""
import calendar
from datetime import date, timedelta
from typing import List, Optional


def calculate_day_intervals(dates: List[date]) -> List[int]:
    """Calculate day differences between consecutive sorted dates.
    
    Args:
        dates: Sorted list of date objects.
        
    Returns:
        List of integers representing elapsed days between successive dates.
    """
    if len(dates) < 2:
        return []
    return [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]


def calculate_calendar_month_difference(d1: date, d2: date) -> int:
    """Calculate the number of calendar months between two dates.
    
    Args:
        d1: Earlier date.
        d2: Later date.
        
    Returns:
        Integer month difference (e.g. 2026-05-10 to 2026-06-10 is 1).
    """
    return (d2.year - d1.year) * 12 + (d2.month - d1.month)


def is_month_end(d: date, tolerance_days: int = 1) -> bool:
    """Check if a date falls on or very near the end of its calendar month.
    
    Args:
        d: Date to inspect.
        tolerance_days: Maximum days before end-of-month to still qualify (default 1).
        
    Returns:
        True if the date is within tolerance_days of the last day of month.
    """
    _, last_day = calendar.monthrange(d.year, d.month)
    return d.day >= (last_day - tolerance_days)


def add_calendar_months(start_date: date, months_to_add: int) -> date:
    """Add a specified number of calendar months to a date, preserving day or clamping to month end.
    
    Args:
        start_date: Starting date.
        months_to_add: Number of months to advance.
        
    Returns:
        New date in the target month.
    """
    new_month = start_date.month + months_to_add
    new_year = start_date.year + (new_month - 1) // 12
    new_month = ((new_month - 1) % 12) + 1
    
    # Clamp day if target month has fewer days
    _, max_days = calendar.monthrange(new_year, new_month)
    new_day = min(start_date.day, max_days)
    
    return date(new_year, new_month, new_day)


def estimate_next_expected_date(
    last_seen_date: date,
    cadence: str,
    median_interval_days: Optional[int] = None,
) -> Optional[date]:
    """Calculate the next estimated payment date based on cadence and last seen date.
    
    Args:
        last_seen_date: Date of the most recent observed transaction.
        cadence: Detected cadence name.
        median_interval_days: Optional median interval in days for irregular cadences.
        
    Returns:
        Estimated date of next charge, or None if unknown/candidate.
    """
    if cadence == "weekly":
        return last_seen_date + timedelta(days=7)
    elif cadence == "fortnightly":
        return last_seen_date + timedelta(days=14)
    elif cadence in ("monthly", "variable_monthly"):
        return add_calendar_months(last_seen_date, 1)
    elif cadence == "quarterly":
        return add_calendar_months(last_seen_date, 3)
    elif cadence == "annual":
        return add_calendar_months(last_seen_date, 12)
    elif cadence == "irregular":
        step = median_interval_days if median_interval_days and median_interval_days > 0 else 30
        return last_seen_date + timedelta(days=step)
    return None
