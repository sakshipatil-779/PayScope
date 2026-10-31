"""Interval analyzer for recurring cadence detection."""
import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import List
from app.analytics.date_utils import (
    calculate_calendar_month_difference,
    calculate_day_intervals,
    is_month_end,
)


@dataclass
class IntervalAnalysis:
    """Statistical summary of transaction intervals."""
    count: int
    intervals: List[int] = field(default_factory=list)
    mean_interval: float = 0.0
    median_interval: float = 0.0
    min_interval: int = 0
    max_interval: int = 0
    std_dev_interval: float = 0.0
    calendar_month_intervals: List[int] = field(default_factory=list)
    is_month_end_pattern: bool = False


def analyze_intervals(dates: List[date]) -> IntervalAnalysis:
    """Analyze time intervals between consecutive dates.
    
    Args:
        dates: List of sorted date objects.
        
    Returns:
        IntervalAnalysis dataclass containing statistical metrics.
    """
    count = len(dates)
    if count < 2:
        return IntervalAnalysis(count=count)

    intervals = calculate_day_intervals(dates)
    month_intervals = [
        calculate_calendar_month_difference(dates[i - 1], dates[i])
        for i in range(1, count)
    ]

    mean_val = float(statistics.mean(intervals))
    median_val = float(statistics.median(intervals))
    min_val = min(intervals)
    max_val = max(intervals)
    stdev_val = float(statistics.stdev(intervals)) if len(intervals) >= 2 else 0.0

    # Check if all or nearly all dates occur near month end
    month_end_count = sum(1 for d in dates if is_month_end(d))
    is_month_end_pattern = (month_end_count / count) >= 0.75

    return IntervalAnalysis(
        count=count,
        intervals=intervals,
        mean_interval=round(mean_val, 2),
        median_interval=round(median_val, 2),
        min_interval=min_val,
        max_interval=max_val,
        std_dev_interval=round(stdev_val, 2),
        calendar_month_intervals=month_intervals,
        is_month_end_pattern=is_month_end_pattern,
    )
