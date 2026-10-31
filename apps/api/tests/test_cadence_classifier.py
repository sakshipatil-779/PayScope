"""Unit tests for cadence classifier."""
from datetime import date
from decimal import Decimal
from app.analytics.amount_analyzer import analyze_amounts
from app.analytics.cadence_classifier import classify_cadence
from app.analytics.interval_analyzer import analyze_intervals


def test_classify_cadence_weekly():
    dates = [
        date(2026, 5, 1),
        date(2026, 5, 8),
        date(2026, 5, 15),
        date(2026, 5, 22),
    ]
    amounts = [Decimal("100.00")] * 4
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "weekly"
    assert res.is_recurring is True
    assert res.is_candidate_only is False


def test_classify_cadence_fortnightly():
    dates = [
        date(2026, 5, 1),
        date(2026, 5, 15),
        date(2026, 5, 29),
        date(2026, 6, 12),
    ]
    amounts = [Decimal("500.00")] * 4
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "fortnightly"
    assert res.is_recurring is True
    assert res.is_candidate_only is False


def test_classify_cadence_monthly_fixed():
    dates = [
        date(2026, 5, 5),
        date(2026, 6, 5),
        date(2026, 7, 5),
        date(2026, 8, 5),
        date(2026, 9, 5),
        date(2026, 10, 5),
    ]
    amounts = [Decimal("499.00")] * 6
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "monthly"
    assert res.is_recurring is True


def test_classify_cadence_variable_monthly():
    dates = [
        date(2026, 5, 8),
        date(2026, 6, 8),
        date(2026, 7, 8),
        date(2026, 8, 8),
        date(2026, 9, 8),
        date(2026, 10, 8),
    ]
    amounts = [Decimal("1420.00"), Decimal("1850.00"), Decimal("1290.00"), Decimal("2100.00"), Decimal("1630.00"), Decimal("1780.00")]
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "variable_monthly"
    assert res.is_recurring is True


def test_classify_cadence_quarterly():
    dates = [
        date(2026, 1, 15),
        date(2026, 4, 15),
        date(2026, 7, 15),
        date(2026, 10, 15),
    ]
    amounts = [Decimal("3000.00")] * 4
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "quarterly"
    assert res.is_recurring is True


def test_classify_cadence_annual_confirmed():
    dates = [
        date(2025, 5, 18),
        date(2026, 5, 18),
    ]
    amounts = [Decimal("14500.00")] * 2
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info, merchant_category="Insurance")
    assert res.cadence == "annual"
    assert res.is_recurring is True
    assert res.is_candidate_only is False


def test_classify_cadence_single_annual_candidate():
    dates = [date(2026, 5, 18)]
    amounts = [Decimal("14500.00")]
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info, merchant_category="Insurance", display_name="Suraksha General Insurance")
    assert res.cadence == "annual"
    assert res.is_recurring is False  # Must NOT be confirmed recurring
    assert res.is_candidate_only is True


def test_classify_cadence_irregular_aquapure():
    dates = [
        date(2026, 5, 4),
        date(2026, 5, 29),
        date(2026, 6, 25),
        date(2026, 7, 20),
        date(2026, 8, 16),
        date(2026, 9, 12),
        date(2026, 10, 8),
    ]
    amounts = [Decimal("650.00")] * 7
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info, merchant_category="Utility", display_name="AquaPure Springs")
    assert res.cadence == "irregular"
    assert res.is_recurring is True


def test_classify_cadence_non_recurring_scattered():
    dates = [
        date(2026, 5, 2),
        date(2026, 5, 6),
        date(2026, 7, 28),
    ]
    amounts = [Decimal("350.00"), Decimal("850.00"), Decimal("120.00")]
    i_info = analyze_intervals(dates)
    a_info = analyze_amounts(amounts)
    res = classify_cadence(i_info, a_info)
    assert res.cadence == "unknown"
    assert res.is_recurring is False
