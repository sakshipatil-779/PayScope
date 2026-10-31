"""Isolated unusual debit amount detector."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.analytics.insights.config import DETECTOR_VERSION, UnusualAmountThresholds
from app.models.commitment import Commitment
from app.models.transaction import Transaction

thresholds = UnusualAmountThresholds()


@dataclass
class UnusualAmountResult:
    """Detected isolated unusual debit within a commitment."""
    commitment_id: str
    unusual_amount: Decimal
    representative_amount: Decimal
    percentage_deviation: Decimal
    transaction_date: datetime
    confidence_score: Decimal
    confidence_band: str
    explanation: str
    detector_version: str = DETECTOR_VERSION
    unusual_transaction: Transaction = None
    baseline_transactions: List[Transaction] = field(default_factory=list)


def detect_unusual_amount(
    commitment: Commitment,
    transactions: List[Transaction],
    price_change_detected: bool = False,
    is_price_increase_detected: bool = False,
) -> List[UnusualAmountResult]:
    """Detect isolated debits that deviate significantly from representative billing.
    
    Rules:
    1. If a sustained price increase is already detected, do not duplicate an alert for the same step.
    2. For stable subscriptions: an isolated charge >= 1.5x representative amount is flagged.
    3. For variable utilities: requires >= 2.5x median to avoid flagging normal consumption variations.
    4. At least 3 total transactions are required for a baseline.
    """
    if price_change_detected or is_price_increase_detected:
        return []

    rep_amount = commitment.representative_amount
    if not rep_amount or rep_amount <= Decimal("0.00"):
        return []

    debits = [
        t for t in transactions
        if t.direction == "debit"
        and t.transaction_status == "successful"
        and t.amount is not None
        and t.amount > Decimal("0.00")
        and t.transaction_date is not None
    ]
    if len(debits) < 3:
        return []

    # Determine multiplier threshold
    is_utility = commitment.commitment_type == "utility"
    multiplier = thresholds.utility_outlier_multiplier if is_utility else thresholds.fixed_cadence_multiplier
    threshold_val = rep_amount * Decimal(str(multiplier))

    # Find the largest outlier charge
    outliers = [t for t in debits if t.amount >= threshold_val]
    if not outliers:
        return []

    # Take the most prominent outlier
    outliers.sort(key=lambda t: t.amount, reverse=True)
    outlier = outliers[0]

    # Baseline transactions are those close to representative amount
    baselines = [t for t in debits if t.id != outlier.id]

    dev_pct = ((outlier.amount - rep_amount) / rep_amount) * Decimal("100")
    score = Decimal("85.00") if not is_utility else Decimal("70.00")
    band = "high" if score >= Decimal("80.00") else "medium"

    explanation = (
        f"Unusual charge of ₹{outlier.amount} observed on "
        f"{outlier.transaction_date.strftime('%d-%b-%Y')} for {commitment.display_name}. "
        f"This is +{dev_pct:.1f}% higher than your usual representative billing amount of ₹{rep_amount}."
    )

    return [
        UnusualAmountResult(
            commitment_id=str(commitment.id),
            unusual_amount=outlier.amount,
            representative_amount=rep_amount,
            percentage_deviation=round(dev_pct, 2),
            transaction_date=outlier.transaction_date,
            confidence_score=score,
            confidence_band=band,
            explanation=explanation,
            detector_version=DETECTOR_VERSION,
            unusual_transaction=outlier,
            baseline_transactions=baselines[:3],
        )
    ]
