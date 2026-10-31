"""Classifier for commitment types based on merchant metadata and descriptors."""
from typing import Optional
from app.models.merchant import Merchant


def classify_commitment_type(
    merchant: Optional[Merchant] = None,
    display_name: str = "",
    is_merchant_resolved: bool = True,
) -> str:
    """Classify the commitment type.
    
    Permitted types:
    - subscription
    - membership
    - utility
    - insurance
    - loan_emi
    - other
    - needs_review
    
    Args:
        merchant: Resolved Merchant model instance if available.
        display_name: Display name or normalised descriptor.
        is_merchant_resolved: False if transaction stream is unresolved/ambiguous.
        
    Returns:
        One of the permitted commitment_type strings.
    """
    if not is_merchant_resolved or merchant is None:
        return "needs_review"

    # 1. Direct override from merchant definition if available
    if merchant.commitment_type_default:
        direct = merchant.commitment_type_default.lower()
        if direct in ("subscription", "membership", "utility", "insurance", "loan_emi", "other", "needs_review"):
            return direct

    cat = (merchant.category or "").lower()
    name = (display_name or merchant.canonical_name or "").lower()

    # 2. Category / keyword classification
    if any(k in cat or k in name for k in ("stream", "entertainment", "software", "saas", "cloud", "ai", "media", "video", "music", "hosting")):
        return "subscription"
    
    if any(k in cat or k in name for k in ("fitness", "gym", "club", "membership", "yoga", "crossfit", "sports")):
        return "membership"

    if any(k in cat or k in name for k in ("utility", "broadband", "telecom", "internet", "fiber", "water", "electricity", "gas", "power")):
        return "utility"

    if any(k in cat or k in name for k in ("insurance", "premium", "policy", "cover")):
        return "insurance"

    if any(k in cat or k in name for k in ("loan", "emi", "lending", "mortgage", "finance", "credit card emi")):
        return "loan_emi"

    return "other"
