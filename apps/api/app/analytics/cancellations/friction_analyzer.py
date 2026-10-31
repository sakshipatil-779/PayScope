"""Friction analyzer evaluating cancellation difficulty and hurdles."""
from typing import Dict, Any
from app.analytics.cancellations.schemas import FrictionLevel, PaymentMechanism, Playbook


def analyze_cancellation_friction(playbook: Playbook) -> Dict[str, Any]:
    """Analyzes cancellation friction factors such as multi-step retention, cooling off periods, or offline requirements."""
    friction_factors = []
    estimated_minutes = 3

    if playbook.payment_mechanism == PaymentMechanism.E_NACH:
        friction_factors.append("Clearing latency: Requires 2-3 business days prior to debit date.")
        friction_factors.append("NetBanking or physical bank form may be required.")
        estimated_minutes = 15
    elif playbook.payment_mechanism == PaymentMechanism.CARD_SI:
        friction_factors.append("Dual cancellation: Merchant platform subscription + Card e-mandate hub.")
        estimated_minutes = 8
    elif playbook.payment_mechanism == PaymentMechanism.UPI_AUTOPAY:
        friction_factors.append("Instantaneous revocation via UPI PIN.")
        estimated_minutes = 3

    if playbook.friction_level == FrictionLevel.HIGH:
        estimated_minutes = max(estimated_minutes, 15)

    return {
        "friction_level": playbook.friction_level.value,
        "estimated_minutes": estimated_minutes,
        "friction_factors": friction_factors,
        "notes": playbook.friction_notes,
    }
