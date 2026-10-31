"""Sustained price increase detection engine."""
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.analytics.insights.config import DETECTOR_VERSION, PriceChangeThresholds
from app.models.commitment import Commitment
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction

thresholds = PriceChangeThresholds()


@dataclass
class PriceIncreaseResult:
    """Detected sustained price increase inside a commitment."""
    commitment_id: str
    previous_amount: Decimal
    new_amount: Decimal
    absolute_change: Decimal
    percentage_change: Decimal
    effective_date: datetime
    confidence_score: Decimal
    confidence_band: str
    explanation: str
    detector_version: str = DETECTOR_VERSION
    old_transactions: List[Transaction] = field(default_factory=list)
    new_transactions: List[Transaction] = field(default_factory=list)
    matching_notification: Optional[PaymentNotification] = None


def detect_price_increase(
    commitment: Commitment,
    transactions: List[Transaction],
    notifications: Optional[List[PaymentNotification]] = None,
) -> Optional[PriceIncreaseResult]:
    """Detect a sustained step price increase within an existing recurring commitment.
    
    Requirements:
    1. Utility bills are excluded from subscription price increase alerts.
    2. At least 2 successful charges in previous price regime.
    3. At least 2 successful charges in new price regime.
    4. Both regimes must exhibit stable amounts (low CV <= 5%).
    5. Percentage increase must be at least 5.0%.
    6. Isolated spikes are ignored (must be sustained).
    
    Args:
        commitment: The Commitment model instance.
        transactions: List of associated transactions.
        notifications: Optional list of user payment notifications.
        
    Returns:
        PriceIncreaseResult if sustained increase is confirmed, else None.
    """
    # Safeguard 1: Protect naturally variable utility commitments
    if commitment.commitment_type == "utility":
        return None

    # Filter successful debits with amount > 0
    debits = [
        t for t in transactions
        if t.direction == "debit"
        and t.transaction_status == "successful"
        and t.amount is not None
        and t.amount > Decimal("0.00")
        and t.transaction_date is not None
    ]
    debits.sort(key=lambda t: (t.transaction_date, str(t.id)))

    min_total = thresholds.min_previous_regime_charges + thresholds.min_new_regime_charges
    if len(debits) < min_total:
        return None

    # Search for a clean step partition split
    # debits[:i] is old regime, debits[i:] is new regime
    found_split: Optional[int] = None
    best_old_median: Optional[Decimal] = None
    best_new_median: Optional[Decimal] = None

    for i in range(thresholds.min_previous_regime_charges, len(debits) - thresholds.min_new_regime_charges + 1):
        old_part = debits[:i]
        new_part = debits[i:]

        old_amts = [float(t.amount) for t in old_part]
        new_amts = [float(t.amount) for t in new_part]

        old_mean = statistics.mean(old_amts)
        new_mean = statistics.mean(new_amts)

        # Regimes must have low variance (stable pricing)
        old_stdev = statistics.stdev(old_amts) if len(old_amts) >= 2 else 0.0
        new_stdev = statistics.stdev(new_amts) if len(new_amts) >= 2 else 0.0

        old_cv = (old_stdev / old_mean) if old_mean > 0 else 0.0
        new_cv = (new_stdev / new_mean) if new_mean > 0 else 0.0

        if old_cv > thresholds.max_regime_cv or new_cv > thresholds.max_regime_cv:
            continue

        old_med = Decimal(str(round(statistics.median(old_amts), 2)))
        new_med = Decimal(str(round(statistics.median(new_amts), 2)))

        if old_med <= Decimal("0.00"):
            continue

        pct_change = ((new_med - old_med) / old_med) * Decimal("100")
        if pct_change >= Decimal(str(thresholds.min_percentage_increase)):
            found_split = i
            best_old_median = old_med
            best_new_median = new_med
            break

    if found_split is None or best_old_median is None or best_new_median is None:
        return None

    old_txns = debits[:found_split]
    new_txns = debits[found_split:]
    effective_dt = new_txns[0].transaction_date

    abs_change = best_new_median - best_old_median
    pct_change = ((best_new_median - best_old_median) / best_old_median) * Decimal("100")

    # Check for supporting price change notification
    matching_notif: Optional[PaymentNotification] = None
    notifs = notifications or []
    for n in notifs:
        if n.event_type == "price_changed":
            # Check merchant hint or text
            hint_match = (
                (n.merchant_hint and n.merchant_hint.lower() in commitment.display_name.lower())
                or (commitment.display_name.lower() in n.message_text.lower())
            )
            if hint_match:
                matching_notif = n
                break

    # Calculate confidence score
    score = Decimal("85.00")
    if matching_notif is not None:
        score = Decimal("95.00")
    elif len(old_txns) >= 3 and len(new_txns) >= 3:
        score = Decimal("90.00")

    conf_band = "high" if score >= Decimal("80.00") else "medium"

    explanation = (
        f"Sustained price increase detected for {commitment.display_name}. "
        f"Billing transitioned from ₹{best_old_median} ({len(old_txns)} billing cycles) "
        f"to ₹{best_new_median} ({len(new_txns)} billing cycles), representing a "
        f"+₹{abs_change} (+{pct_change:.1f}%) recurring increase effective {effective_dt.strftime('%d-%b-%Y')}."
    )
    if matching_notif:
        explanation += " Corroborated by merchant price update notification."

    return PriceIncreaseResult(
        commitment_id=str(commitment.id),
        previous_amount=best_old_median,
        new_amount=best_new_median,
        absolute_change=abs_change,
        percentage_change=round(pct_change, 2),
        effective_date=effective_dt,
        confidence_score=score,
        confidence_band=conf_band,
        explanation=explanation,
        detector_version=DETECTOR_VERSION,
        old_transactions=old_txns,
        new_transactions=new_txns,
        matching_notification=matching_notif,
    )


# Alias for naming consistency
detect_price_increases = detect_price_increase
