"""Unit tests for amount analyzer."""
from decimal import Decimal
from app.analytics.amount_analyzer import analyze_amounts


def test_analyze_amounts_empty_and_single():
    res0 = analyze_amounts([])
    assert res0.count == 0
    assert res0.amount_pattern == "insufficient_data"

    res1 = analyze_amounts([Decimal("499.00")])
    assert res1.count == 1
    assert res1.representative_amount == Decimal("499.00")
    assert res1.amount_pattern == "insufficient_data"


def test_analyze_amounts_fixed():
    amounts = [Decimal("499.00")] * 6
    res = analyze_amounts(amounts)
    assert res.count == 6
    assert res.representative_amount == Decimal("499.00")
    assert res.amount_min == Decimal("499.00")
    assert res.amount_max == Decimal("499.00")
    assert res.amount_pattern == "fixed"
    assert res.has_price_change is False
    assert res.cv == 0.0


def test_analyze_amounts_variable_price_hike():
    amounts = [
        Decimal("799.00"),
        Decimal("799.00"),
        Decimal("799.00"),
        Decimal("999.00"),
        Decimal("999.00"),
        Decimal("999.00"),
    ]
    res = analyze_amounts(amounts)
    assert res.count == 6
    assert res.representative_amount == Decimal("899.00")
    assert res.amount_min == Decimal("799.00")
    assert res.amount_max == Decimal("999.00")
    assert res.amount_pattern == "variable"
    assert res.has_price_change is True
    assert res.cv > 0.05


def test_analyze_amounts_variable_utility():
    amounts = [
        Decimal("1420.00"),
        Decimal("1850.00"),
        Decimal("1290.00"),
        Decimal("2100.00"),
        Decimal("1630.00"),
        Decimal("1780.00"),
    ]
    res = analyze_amounts(amounts)
    assert res.count == 6
    assert res.amount_pattern == "variable"
    assert res.amount_min == Decimal("1290.00")
    assert res.amount_max == Decimal("2100.00")
