"""Unit tests for the 6-stage merchant matching and ambiguity detection engine."""
import uuid
import pytest
from app.matching.config import DEFAULT_MATCHING_CONFIG
from app.matching.merchant_fixtures import CANONICAL_MERCHANT_REGISTRY
from app.matching.normalizer import DescriptorNormalizer
from app.matching.regex_matcher import RegexMatcher
from app.matching.resolver import MerchantResolver
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


@pytest.fixture
def in_memory_merchants_and_aliases():
    """Create in-memory Merchant and DescriptorAlias model instances for testing."""
    merchants = []
    aliases = []

    for fix in CANONICAL_MERCHANT_REGISTRY:
        m = Merchant(
            id=uuid.uuid4(),
            canonical_name=fix.canonical_name,
            category=fix.category,
            commitment_type_default=fix.commitment_type_default,
            is_fictional_demo_merchant=fix.is_fictional,
        )
        merchants.append(m)

        for a in fix.aliases:
            norm_a = DescriptorNormalizer.normalize(a.alias_text)
            al = DescriptorAlias(
                id=uuid.uuid4(),
                merchant_id=m.id,
                alias_text=a.alias_text,
                normalised_alias=norm_a,
                matcher_type=a.matcher_type,
                pattern=a.pattern,
                confidence_band=a.confidence_band,
                is_active=True,
            )
            aliases.append(al)

    return merchants, aliases


def test_stage1_exact_canonical_match(in_memory_merchants_and_aliases):
    """Stage 1: Descriptor matching the canonical name exactly produces MATCHED_HIGH."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    res = resolver.resolve("StreamPulse Entertainment")
    assert res.status == "MATCHED_HIGH"
    assert res.merchant_name == "StreamPulse Entertainment"
    assert res.score == 100.0
    assert res.match_method == "exact_canonical"
    assert res.confidence_band == "high"


def test_stage2_exact_alias_match(in_memory_merchants_and_aliases):
    """Stage 2: Descriptor matching a known curated alias produces MATCHED_HIGH."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    res = resolver.resolve("UPI/STREAMPULSE/BILLPAY/982138")
    assert res.status == "MATCHED_HIGH"
    assert res.merchant_name == "StreamPulse Entertainment"
    assert res.score == 100.0
    assert res.match_method == "exact_alias"


def test_stage3_token_and_prefix_match(in_memory_merchants_and_aliases):
    """Stage 3: Token pattern matches when distinct alias tokens are present."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    # Contains "quickcab" token
    res = resolver.resolve("ACH DEBIT QUICKCAB COMMUTE FARE 4910")
    assert res.status == "MATCHED_HIGH"
    assert res.merchant_name == "QuickCab Monthly Pass"
    assert res.confidence_band == "high"


def test_stage4_rapidfuzz_fuzzy_match(in_memory_merchants_and_aliases):
    """Stage 4: Typographical noise or token jitter resolves via RapidFuzz."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    # Slight typo: CloudDeskk Pro Subscrptn
    res = resolver.resolve("CLOUDDESKK PRO SUBSCRPTN")
    assert res.status in ("MATCHED_HIGH", "MATCHED_MEDIUM")
    assert res.merchant_name == "CloudDesk Pro"
    assert res.score >= 80.0


def test_stage5_generic_aggregator_needs_review(in_memory_merchants_and_aliases):
    """Scenario 12: Generic payment aggregator descriptors must route to NEEDS_REVIEW."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    res = resolver.resolve("BILLDESK*PG-MUMBAI-TXN99281")
    assert res.status == "NEEDS_REVIEW"
    assert res.is_ambiguous is True
    assert "aggregator" in res.explanation.lower()

    res2 = resolver.resolve("RAZORPAY*MERCH_INTL_4819")
    assert res2.status == "NEEDS_REVIEW"
    assert res2.is_ambiguous is True


def test_unresolved_unknown_descriptor(in_memory_merchants_and_aliases):
    """Unrecognized random descriptor without matching candidates is UNRESOLVED."""
    merchants, aliases = in_memory_merchants_and_aliases
    resolver = MerchantResolver(merchants=merchants, aliases=aliases)

    res = resolver.resolve("XYZ UNKNOWN MYSTERY TRADING CO 99281")
    assert res.status == "UNRESOLVED"
    assert res.merchant_id is None
    assert res.confidence_band == "none"


def test_regex_safety_and_validation():
    """Verify regex pattern validation rejects dangerous or malformed expressions."""
    # Malformed regex
    is_valid, err = RegexMatcher.validate_pattern("[a-z", DEFAULT_MATCHING_CONFIG)
    assert not is_valid
    assert "syntax" in err.lower()

    # Catastrophic backtracking
    is_valid, err = RegexMatcher.validate_pattern("((a+)+)+", DEFAULT_MATCHING_CONFIG)
    assert not is_valid
    assert "catastrophic" in err.lower()

    # Valid regex
    is_valid, err = RegexMatcher.validate_pattern(r"^UPI\s*STREAMPULSE", DEFAULT_MATCHING_CONFIG)
    assert is_valid
    assert err is None
