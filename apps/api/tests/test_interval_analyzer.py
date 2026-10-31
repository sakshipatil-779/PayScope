"""Unit tests for interval analyzer and date utilities."""
from datetime import date
from app.analytics.date_utils import (
    add_calendar_months,
    calculate_calendar_month_difference,
    calculate_day_intervals,
    estimate_next_expected_date,
    is_month_end,
)
from app.analytics.interval_analyzer import analyze_intervals


def test_calculate_day_intervals():
    dates = [
        date(2026, 5, 5),
        date(2026, 6, 5),
        date(2026, 7, 5),
    ]
    intervals = calculate_day_intervals(dates)
    assert intervals == [31, 30]


def test_calculate_calendar_month_difference():
    d1 = date(2026, 5, 10)
    d2 = date(2026, 6, 10)
    d3 = date(2027, 5, 10)
    assert calculate_calendar_month_difference(d1, d2) == 1
    assert calculate_calendar_month_difference(d1, d3) == 12


def test_is_month_end():
    assert is_month_end(date(2026, 5, 31)) is True
    assert is_month_end(date(2026, 5, 30)) is True
    assert is_month_end(date(2026, 5, 15)) is False
    assert is_month_end(date(2026, 2, 28)) is True


def test_add_calendar_months_month_end():
    d = date(2026, 1, 31)
    next_m = add_calendar_months(d, 1)
    assert next_m == date(2026, 2, 28)

    d2 = date(2026, 5, 15)
    assert add_calendar_months(d2, 1) == date(2026, 6, 15)
    assert add_calendar_months(d2, 3) == date(2026, 8, 15)
    assert add_calendar_months(d2, 12) == date(2027, 5, 15)


def test_estimate_next_expected_date():
    d = date(2026, 10, 5)
    assert estimate_next_expected_date(d, "weekly") == date(2026, 10, 12)
    assert estimate_next_expected_date(d, "fortnightly") == date(2026, 10, 19)
    assert estimate_next_expected_date(d, "monthly") == date(2026, 11, 5)
    assert estimate_next_expected_date(d, "quarterly") == date(2027, 1, 5)
    assert estimate_next_expected_date(d, "annual") == date(2027, 10, 5)
    assert estimate_next_expected_date(d, "irregular", median_interval_days=25) == date(2026, 10, 30)


def test_analyze_intervals_empty_and_single():
    res0 = analyze_intervals([])
    assert res0.count == 0
    assert res0.median_interval == 0.0

    res1 = analyze_intervals([date(2026, 5, 1)])
    assert res1.count == 1
    assert res1.median_interval == 0.0


def test_analyze_intervals_monthly():
    dates = [
        date(2026, 5, 5),
        date(2026, 6, 5),
        date(2026, 7, 5),
        date(2026, 8, 5),
        date(2026, 9, 5),
        date(2026, 10, 5),
    ]
    res = analyze_intervals(dates)
    assert res.count == 6
    assert 30 <= res.median_interval <= 31
    assert res.std_dev_interval <= 1.0
    assert res.calendar_month_intervals == [1, 1, 1, 1, 1]
