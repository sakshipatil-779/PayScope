"""Post-cancellation charge detection engine."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from app.analytics.insights.config import DETECTOR_VERSION
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction


@dataclass
class PostCancellationResult:
    """Detected debit occurring after recorded cancellation."""
    commitment_id: str
    cancellation_date: datetime
    first_post_charge_date: datetime
    post_charge_amount: Decimal
    confirmation_type: str  # explicit_notification, user_confirmed, inferred_needs_review
    confidence_score: Decimal
    confidence_band: str
    explanation: str
    detector_version: str = DETECTOR_VERSION
    post_transactions: List[Transaction] = field(default_factory=list)
    cancellation_event: Optional[CancellationEvent] = None
    cancellation_notification: Optional[PaymentNotification] = None


def detect_post_cancellation_charge(
    commitment: Commitment,
    transactions: List[Transaction],
    cancellation_events: Optional[List[CancellationEvent]] = None,
    notifications: Optional[List[PaymentNotification]] = None,
) -> Optional[PostCancellationResult]:
    """Detect successful debits occurring after an established cancellation event.
    
    Rules:
    1. Identify a valid cancellation record (event or subscription_cancelled notification).
    2. Find subsequent successful debits strictly dated AFTER the cancellation timestamp.
    3. Exclude failed or reversed debits.
    4. Distinguish between explicit provider notifications and user-recorded confirmations.
    5. Avoid inflammatory language (no 'fraud', 'theft').
    
    Args:
        commitment: The Commitment model instance.
        transactions: List of associated transactions.
        cancellation_events: Optional list of CancellationEvent records.
        notifications: Optional list of user payment notifications.
        
    Returns:
        PostCancellationResult if post-cancellation debit is confirmed, else None.
    """
    cancel_dt: Optional[datetime] = None
    conf_type = "explicit_notification"
    matched_event: Optional[CancellationEvent] = None
    matched_notif: Optional[PaymentNotification] = None

    # Check dedicated cancellation events first
    if cancellation_events:
        for ce in cancellation_events:
            cancel_dt = ce.event_timestamp
            conf_type = ce.confirmation_type
            matched_event = ce
            break

    # If no dedicated event, check notifications for cancellation confirmations
    if cancel_dt is None and notifications:
        for n in notifications:
            if n.event_type in ("subscription_cancelled", "mandate_revoked"):
                hint_match = (
                    (n.merchant_hint and n.merchant_hint.lower() in commitment.display_name.lower())
                    or (commitment.display_name.lower() in n.message_text.lower())
                )
                if hint_match:
                    cancel_dt = n.event_timestamp
                    conf_type = "explicit_notification"
                    matched_notif = n
                    break

    if cancel_dt is None:
        return None

    # Search for subsequent successful debits with amount > 0
    post_charges = [
        t for t in transactions
        if t.direction == "debit"
        and t.transaction_status == "successful"
        and t.amount is not None
        and t.amount > Decimal("0.00")
        and t.transaction_date > cancel_dt
    ]
    post_charges.sort(key=lambda t: (t.transaction_date, str(t.id)))

    if not post_charges:
        return None

    first_charge = post_charges[0]
    score = Decimal("95.00")
    band = "high"

    # Contextual wording based on evidence source
    if conf_type == "user_confirmed":
        desc_phrase = "your recorded cancellation confirmation"
    elif conf_type == "explicit_notification":
        desc_phrase = "a recorded provider cancellation notification"
    else:
        desc_phrase = "recorded cancellation evidence"

    explanation = (
        f"Another successful charge of ₹{first_charge.amount} was detected on "
        f"{first_charge.transaction_date.strftime('%d-%b-%Y')} for {commitment.display_name} "
        f"after {desc_phrase} from {cancel_dt.strftime('%d-%b-%Y')}."
    )

    return PostCancellationResult(
        commitment_id=str(commitment.id),
        cancellation_date=cancel_dt,
        first_post_charge_date=first_charge.transaction_date,
        post_charge_amount=first_charge.amount,
        confirmation_type=conf_type,
        confidence_score=score,
        confidence_band=band,
        explanation=explanation,
        detector_version=DETECTOR_VERSION,
        post_transactions=post_charges,
        cancellation_event=matched_event,
        cancellation_notification=matched_notif,
    )


# Alias for naming consistency
detect_post_cancellation = detect_post_cancellation_charge
