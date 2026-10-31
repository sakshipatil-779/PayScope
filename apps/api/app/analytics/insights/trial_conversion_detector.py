"""Free trial to paid conversion detection engine."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.analytics.insights.config import DETECTOR_VERSION
from app.models.commitment import Commitment
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction


@dataclass
class TrialConversionResult:
    """Detected trial conversion inside a commitment."""
    commitment_id: str
    trial_start_date: datetime
    conversion_date: datetime
    first_paid_amount: Decimal
    confidence_score: Decimal
    confidence_band: str
    explanation: str
    detector_version: str = DETECTOR_VERSION
    trial_notification: PaymentNotification = None
    converted_transaction: Transaction = None
    subsequent_transactions: List[Transaction] = field(default_factory=list)


def detect_trial_conversion(
    commitment: Commitment,
    transactions: List[Transaction],
    notifications: List[PaymentNotification],
) -> Optional[TrialConversionResult]:
    """Detect free trial converting into a recurring paid subscription.
    
    Rules:
    1. Identify a valid 'trial_started' notification matching the commitment.
    2. Find the first subsequent successful debit with amount > 0.
    3. Zero-dollar authorizations do NOT qualify as conversion evidence.
    4. Link the trial notification and converted transaction evidence.
    
    Args:
        commitment: The Commitment model instance.
        transactions: List of associated transactions.
        notifications: List of user payment notifications.
        
    Returns:
        TrialConversionResult if conversion is confirmed, else None.
    """
    # 1. Search for a matching trial_started notification
    trial_notif: Optional[PaymentNotification] = None
    for n in notifications:
        if n.event_type == "trial_started":
            hint_match = (
                (n.merchant_hint and n.merchant_hint.lower() in commitment.display_name.lower())
                or (commitment.display_name.lower() in n.message_text.lower())
            )
            if hint_match:
                trial_notif = n
                break

    if trial_notif is None:
        return None

    # 2. Look for subsequent successful debits with amount > 0
    trial_dt = trial_notif.event_timestamp
    paid_debits = [
        t for t in transactions
        if t.direction == "debit"
        and t.transaction_status == "successful"
        and t.amount is not None
        and t.amount > Decimal("0.00")
        and t.transaction_date >= trial_dt
    ]
    paid_debits.sort(key=lambda t: (t.transaction_date, str(t.id)))

    if not paid_debits:
        # Trial started but no paid debit has occurred yet
        return None

    first_paid = paid_debits[0]
    conversion_dt = first_paid.transaction_date
    first_amt = first_paid.amount

    score = Decimal("95.00")
    conf_band = "high"

    explanation = (
        f"Your {commitment.display_name} trial appears to have converted into a paid subscription. "
        f"The first successful charge of ₹{first_amt} was observed on "
        f"{conversion_dt.strftime('%d-%b-%Y')} following trial activation on {trial_dt.strftime('%d-%b-%Y')}."
    )

    return TrialConversionResult(
        commitment_id=str(commitment.id),
        trial_start_date=trial_dt,
        conversion_date=conversion_dt,
        first_paid_amount=first_amt,
        confidence_score=score,
        confidence_band=conf_band,
        explanation=explanation,
        detector_version=DETECTOR_VERSION,
        trial_notification=trial_notif,
        converted_transaction=first_paid,
        subsequent_transactions=paid_debits[1:],
    )
