"""Unit tests for commitment type classifier."""
from app.analytics.commitment_classifier import classify_commitment_type
from app.models.merchant import Merchant


def test_classify_commitment_type():
    m_sub = Merchant(canonical_name="StreamPulse Entertainment", category="Streaming Video")
    assert classify_commitment_type(m_sub, "StreamPulse") == "subscription"

    m_fit = Merchant(canonical_name="Zenith Fitness Club", category="Gym & Fitness")
    assert classify_commitment_type(m_fit, "Zenith Fitness") == "membership"

    m_util = Merchant(canonical_name="FiberNet Broadband", category="Broadband & Telecom")
    assert classify_commitment_type(m_util, "FiberNet") == "utility"

    m_ins = Merchant(canonical_name="Suraksha General Insurance", category="General Insurance")
    assert classify_commitment_type(m_ins, "Suraksha") == "insurance"

    # Unresolved merchant goes to needs_review
    assert classify_commitment_type(None, "UNKNOWN_DESCRIPTOR", is_merchant_resolved=False) == "needs_review"
