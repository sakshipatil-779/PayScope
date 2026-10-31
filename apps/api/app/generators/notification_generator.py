"""Synthetic payment notification generator logic."""
import random
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List
from faker import Faker
from app.generators.config import GeneratorConfig


def generate_notifications(config: GeneratorConfig, fake: Faker) -> List[Dict[str, Any]]:
    """Generate reproducible synthetic payment and mandate notifications."""
    rng = random.Random(config.seed + 100)
    notifications: List[Dict[str, Any]] = []
    notif_counter = 1

    def make_notif(
        ts: datetime,
        event_type: str,
        merchant_hint: str,
        amount: float = None,
        mechanism: str = None,
        mandate_ref: str = None,
        message: str = "",
        scenario_key: str = None,
    ) -> Dict[str, Any]:
        nonlocal notif_counter
        ext_id = f"SYN-NOTIF-{config.seed:04d}-{notif_counter:04d}"
        notif_counter += 1
        amt_val = float(Decimal(str(amount)).quantize(Decimal("0.01"))) if amount is not None else None
        return {
            "external_synthetic_id": ext_id,
            "event_timestamp": ts.isoformat(),
            "event_type": event_type,
            "merchant_hint": merchant_hint,
            "amount": amt_val,
            "currency": config.currency if amt_val is not None else None,
            "payment_mechanism": mechanism,
            "mandate_external_ref": mandate_ref,
            "message_text": message,
            "scenario_key": scenario_key,
            "is_synthetic": True,
        }

    # 1. StreamPulse - Mandate Created
    notifications.append(
        make_notif(
            datetime(2026, 5, 1, 10, 30, tzinfo=timezone.utc),
            "mandate_created",
            "StreamPulse",
            amount=499.00,
            mechanism="upi_autopay",
            mandate_ref="UMN/STRP/2026/0129",
            message="UPI AutoPay mandate created for StreamPulse Entertainment for Rs 499.00/month. UMN: UMN/STRP/2026/0129.",
            scenario_key="scenario_1_dual_descriptor",
        )
    )

    # 2. StreamPulse - Payment Success (May)
    notifications.append(
        make_notif(
            datetime(2026, 5, 5, 11, 15, tzinfo=timezone.utc),
            "payment_success",
            "StreamPulse",
            amount=499.00,
            mechanism="upi",
            message="Auto-debit successful: Rs 499.00 paid to StreamPulse Entertainment under mandate UMN/STRP/2026/0129.",
            scenario_key="scenario_1_dual_descriptor",
        )
    )

    # 3. CloudDesk Pro - Price Change Notification (Scenario 2)
    notifications.append(
        make_notif(
            datetime(2026, 7, 28, 14, 0, tzinfo=timezone.utc),
            "price_changed",
            "CloudDesk Pro",
            amount=999.00,
            mechanism="card",
            message="Notice: Your CloudDesk Pro monthly subscription plan price will update from Rs 799 to Rs 999 starting with your August 2026 billing cycle.",
            scenario_key="scenario_2_price_increase",
        )
    )

    # 4. SynthWrite AI - Trial Started (Scenario 3)
    notifications.append(
        make_notif(
            datetime(2026, 5, 10, 9, 0, tzinfo=timezone.utc),
            "trial_started",
            "SynthWrite AI",
            amount=0.00,
            mechanism="upi_autopay",
            mandate_ref="UMN/SYNTH/2026/8812",
            message="Welcome to SynthWrite AI! Your 14-day free trial has begun. First recurring billing of Rs 1,299 will occur on 24-May-2026 unless cancelled.",
            scenario_key="scenario_3_trial_conversion",
        )
    )

    # 5. SynthWrite AI - First Paid Conversion (Scenario 3)
    notifications.append(
        make_notif(
            datetime(2026, 5, 24, 10, 0, tzinfo=timezone.utc),
            "payment_success",
            "SynthWrite AI",
            amount=1299.00,
            mechanism="upi_autopay",
            mandate_ref="UMN/SYNTH/2026/8812",
            message="Your SynthWrite AI Pro subscription has renewed for Rs 1,299.00. Mandate reference: UMN/SYNTH/2026/8812.",
            scenario_key="scenario_3_trial_conversion",
        )
    )

    # 6. Zenith Fitness Club - Membership Welcome & Card Recurring (Scenario 4)
    notifications.append(
        make_notif(
            datetime(2026, 5, 1, 8, 45, tzinfo=timezone.utc),
            "payment_success",
            "Zenith Fitness Club",
            amount=2499.00,
            mechanism="card",
            message="Membership payment of Rs 2,499.00 for Zenith Fitness Club Indiranagar processed successfully via card ending in 4102.",
            scenario_key="scenario_4_unused_membership",
        )
    )

    # 7. SkyVault Backup - Subscription Cancellation Confirmation (Scenario 5)
    notifications.append(
        make_notif(
            datetime(2026, 7, 20, 16, 20, tzinfo=timezone.utc),
            "subscription_cancelled",
            "SkyVault Backup",
            amount=None,
            mechanism="card",
            message="Your cancellation request for SkyVault Backup has been processed. Your subscription will end on 31-Jul-2026 and no further charges will apply.",
            scenario_key="scenario_5_post_cancel_charge",
        )
    )

    # 8. Suraksha General Insurance - Annual Premium Renewal (Scenario 6)
    notifications.append(
        make_notif(
            datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
            "payment_success",
            "Suraksha General Insurance",
            amount=14500.00,
            mechanism="bank_transfer",
            message="Policy renewal confirmed: Rs 14,500.00 received for Suraksha Health Shield (Policy #SUR-99214). Coverage valid until May 2027.",
            scenario_key="scenario_6_annual_insurance",
        )
    )

    # 9. FiberNet Broadband - Payment Success (Scenario 7)
    notifications.append(
        make_notif(
            datetime(2026, 5, 8, 18, 10, tzinfo=timezone.utc),
            "payment_success",
            "FiberNet Broadband",
            amount=1420.00,
            mechanism="upi",
            message="Payment of Rs 1,420.00 for FiberNet Broadband Account #FN-88190 received. Thank you.",
            scenario_key="scenario_7_variable_utility",
        )
    )

    # 10. CineFlow Premium - Payment Success (Scenario 8a)
    notifications.append(
        make_notif(
            datetime(2026, 5, 10, 15, 30, tzinfo=timezone.utc),
            "payment_success",
            "CineFlow Premium",
            amount=649.00,
            mechanism="upi",
            message="Your CineFlow Premium 4K plan has renewed for Rs 649.00.",
            scenario_key="scenario_8_category_overlap_a",
        )
    )

    # 11. IndieWatch Movies - Payment Success (Scenario 8b)
    notifications.append(
        make_notif(
            datetime(2026, 5, 18, 17, 0, tzinfo=timezone.utc),
            "payment_success",
            "IndieWatch Movies",
            amount=299.00,
            mechanism="upi",
            message="IndieWatch Movies subscription charged Rs 299.00 via UPI.",
            scenario_key="scenario_8_category_overlap_b",
        )
    )

    # 12. QuickCab Monthly Pass - Mandate Registered with Higher Limit (Scenario 9)
    notifications.append(
        make_notif(
            datetime(2026, 5, 2, 9, 15, tzinfo=timezone.utc),
            "mandate_created",
            "QuickCab Monthly Pass",
            amount=5000.00,  # Max limit registered on mandate
            mechanism="upi_autopay",
            mandate_ref="UMN/QC/2026/99812",
            message="UPI AutoPay Mandate created for QuickCab Mobility. Max limit: Rs 5,000.00. Regular cycle debit: Rs 1,999.00. UMN: UMN/QC/2026/99812.",
            scenario_key="scenario_9_autopay_high_limit",
        )
    )

    # 13. QuickCab Monthly Pass - Regular Monthly Debit (Scenario 9)
    notifications.append(
        make_notif(
            datetime(2026, 5, 2, 9, 20, tzinfo=timezone.utc),
            "payment_success",
            "QuickCab Monthly Pass",
            amount=1999.00,
            mechanism="upi_autopay",
            mandate_ref="UMN/QC/2026/99812",
            message="Auto-debit successful: Rs 1,999.00 debited for QuickCab Pass under mandate UMN/QC/2026/99812.",
            scenario_key="scenario_9_autopay_high_limit",
        )
    )

    # 14. DevStack Cloud Hosting - Card Mandate Created (Scenario 11)
    notifications.append(
        make_notif(
            datetime(2026, 5, 3, 11, 0, tzinfo=timezone.utc),
            "mandate_created",
            "DevStack Cloud Hosting",
            amount=3499.00,
            mechanism="card_mandate",
            mandate_ref="SI/DEVSTK/CC/4102",
            message="Standing instruction registered on Card **4102 for DevStack Cloud Hosting. Recurring amount: Rs 3,499.00/month.",
            scenario_key="scenario_11_card_mandate",
        )
    )

    # 15. DevStack Cloud Hosting - Payment Success (Scenario 11)
    notifications.append(
        make_notif(
            datetime(2026, 5, 3, 11, 5, tzinfo=timezone.utc),
            "payment_success",
            "DevStack Cloud Hosting",
            amount=3499.00,
            mechanism="card_mandate",
            mandate_ref="SI/DEVSTK/CC/4102",
            message="Recurring card debit of Rs 3,499.00 processed for DevStack Cloud Hosting Mumbai.",
            scenario_key="scenario_11_card_mandate",
        )
    )

    # 16. Simulated Mandate Paused event
    notifications.append(
        make_notif(
            datetime(2026, 8, 10, 14, 30, tzinfo=timezone.utc),
            "mandate_paused",
            "StreamPulse",
            amount=499.00,
            mechanism="upi_autopay",
            mandate_ref="UMN/STRP/2026/0129",
            message="UPI AutoPay mandate UMN/STRP/2026/0129 for StreamPulse has been paused per your request.",
            scenario_key="scenario_1_dual_descriptor",
        )
    )

    # 17. Simulated Mandate Revoked event
    notifications.append(
        make_notif(
            datetime(2026, 8, 20, 16, 45, tzinfo=timezone.utc),
            "mandate_revoked",
            "SkyVault Backup",
            amount=None,
            mechanism="upi_autopay",
            mandate_ref="UMN/SKYV/2026/0014",
            message="Mandate UMN/SKYV/2026/0014 has been permanently revoked. No further auto-debits will be permitted.",
            scenario_key="scenario_5_post_cancel_charge",
        )
    )

    # 18. Payment failed retry event
    notifications.append(
        make_notif(
            datetime(2026, 6, 12, 10, 5, tzinfo=timezone.utc),
            "payment_failed",
            "CloudDesk Pro",
            amount=799.00,
            mechanism="card",
            message="Recurring charge attempt of Rs 799.00 for CloudDesk Pro failed due to network timeout. System will retry in 24 hours.",
            scenario_key="scenario_2_price_increase",
        )
    )

    # Sort deterministically
    notifications.sort(key=lambda n: (n["event_timestamp"], n["external_synthetic_id"]))
    return notifications
