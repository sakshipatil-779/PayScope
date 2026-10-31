"""Tests for descriptor normalisation engine."""
from app.matching.normalizer import DescriptorNormalizer


def test_normalizer_trim_and_lowercase():
    """Verify whitespace trimming and case standardisation."""
    raw = "   UPI/STREAMPULSE/BILLPAY/982138   "
    expected = "upi streampulse billpay 982138"
    assert DescriptorNormalizer.normalize(raw) == expected


def test_normalizer_multiple_separators():
    """Verify replacement of slashes, hyphens, underscores, asterisks, dots."""
    raw = "RAZORPAY*CLOUDDESK_BLR-IND.TXN/99"
    expected = "razorpay clouddesk blr ind txn 99"
    assert DescriptorNormalizer.normalize(raw) == expected


def test_normalizer_unicode_safety():
    """Verify Unicode accents are safely decomposed without throwing."""
    raw = "Café Roast Spécial"
    normalized = DescriptorNormalizer.normalize(raw)
    assert "cafe roast special" in normalized or "cafe" in normalized


def test_normalizer_preserves_numeric_identifiers():
    """Verify transaction and mandate reference numbers are kept intact."""
    raw = "UPI/SYNTHWRITE/AUTOPAY/88129"
    normalized = DescriptorNormalizer.normalize(raw)
    assert "88129" in normalized
    assert "synthwrite" in normalized
    assert "autopay" in normalized


def test_normalizer_empty_and_null_descriptors():
    """Verify None, empty strings, and whitespace return empty string."""
    assert DescriptorNormalizer.normalize(None) == ""
    assert DescriptorNormalizer.normalize("") == ""
    assert DescriptorNormalizer.normalize("     ") == ""


def test_normalizer_bounded_length():
    """Verify excessively long malicious inputs are safely bounded."""
    huge_input = "A" * 2000
    normalized = DescriptorNormalizer.normalize(huge_input)
    assert len(normalized) <= 500


def test_extract_tokens():
    """Verify token extraction utility."""
    tokens = DescriptorNormalizer.extract_tokens("upi streampulse billpay 982138")
    assert tokens == ["upi", "streampulse", "billpay", "982138"]
    assert DescriptorNormalizer.extract_tokens("") == []
