"""Mechanism classifier to deduce the likely recurring payment channel."""
from typing import List, Optional, Tuple
from app.analytics.cancellations.schemas import PaymentMechanism
from app.models.commitment import Commitment
from app.models.transaction import Transaction


def classify_payment_mechanism(
    commitment: Commitment,
    transactions: Optional[List[Transaction]] = None,
) -> Tuple[PaymentMechanism, float]:
    """Classifies the payment mechanism based on transaction patterns, descriptors and channels.

    Returns:
        Tuple of (PaymentMechanism, confidence_score)
    """
    if not transactions:
        # Check commitment's own transactions relationship if loaded
        if hasattr(commitment, "transactions") and commitment.transactions:
            transactions = [ct.transaction for ct in commitment.transactions if ct.transaction]
        else:
            transactions = []

    if not transactions:
        return PaymentMechanism.UNKNOWN, 0.0

    upi_votes = 0
    card_votes = 0
    enach_votes = 0
    total_samples = len(transactions)

    upi_keywords = ["UPI", "AUTOPAY", "VPA", "@OK", "@UPI", "@PAYTM", "@AXIS", "@YBL", "@IBL"]
    card_keywords = ["CARD", "POS", "VISA", "MASTERCARD", "SI", "E-COM", "DEBIT", "CREDIT", "SI-CARD"]
    enach_keywords = ["NACH", "ACH", "ENACH", "E-NACH", "MANDATE", "ECS", "CLEARING", "UMRN"]

    for tx in transactions:
        channel = (tx.payment_channel or "").upper()
        raw = (tx.raw_descriptor or "").upper()
        norm = (tx.normalised_descriptor or "").upper()
        text_corpus = f"{channel} {raw} {norm}"

        if any(kw in text_corpus for kw in upi_keywords) or channel == "UPI":
            upi_votes += 1
        elif any(kw in text_corpus for kw in enach_keywords) or channel in ("NACH", "ENACH", "ECS"):
            enach_votes += 1
        elif any(kw in text_corpus for kw in card_keywords) or channel in ("CARD", "DEBIT_CARD", "CREDIT_CARD"):
            card_votes += 1

    max_votes = max(upi_votes, card_votes, enach_votes)
    if max_votes == 0:
        return PaymentMechanism.OTHER, 0.3

    confidence = round(max_votes / total_samples, 2)

    if upi_votes == max_votes:
        return PaymentMechanism.UPI_AUTOPAY, min(confidence + 0.1, 1.0)
    elif enach_votes == max_votes:
        return PaymentMechanism.E_NACH, min(confidence + 0.1, 1.0)
    elif card_votes == max_votes:
        return PaymentMechanism.CARD_SI, min(confidence + 0.1, 1.0)

    return PaymentMechanism.OTHER, 0.5
