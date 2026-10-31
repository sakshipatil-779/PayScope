"""Synthetic transaction generation logic."""
import random
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List
from faker import Faker
from app.generators.config import GeneratorConfig
from app.generators.merchant_fixtures import ONE_OFF_MERCHANTS, SCENARIO_MERCHANTS


def generate_transactions(config: GeneratorConfig, fake: Faker) -> List[Dict[str, Any]]:
    """Generate reproducible list of synthetic transactions meeting all 12 scenarios."""
    rng = random.Random(config.seed)
    transactions: List[Dict[str, Any]] = []
    txn_counter = 1

    def make_txn(
        txn_date: date,
        raw_desc: str,
        amount: float,
        channel: str,
        scenario_key: str,
        direction: str = "debit",
        norm_desc: str = None,
    ) -> Dict[str, Any]:
        nonlocal txn_counter
        ext_id = f"SYN-TXN-{config.seed:04d}-{txn_counter:05d}"
        ref = f"SYNREF{config.seed}{txn_counter:06d}"
        txn_counter += 1

        dt = datetime.combine(txn_date, time(hour=rng.randint(8, 21), minute=rng.randint(0, 59)), tzinfo=timezone.utc)
        return {
            "external_synthetic_id": ext_id,
            "transaction_date": dt.isoformat(),
            "date": txn_date.strftime("%Y-%m-%d"),
            "raw_descriptor": raw_desc,
            "normalised_descriptor": norm_desc or raw_desc.strip(),
            "amount": float(Decimal(str(amount)).quantize(Decimal("0.01"))),
            "currency": config.currency,
            "direction": direction,
            "transaction_status": "successful",
            "payment_channel": channel,
            "payment_reference": ref,
            "scenario_key": scenario_key,
            "is_synthetic": True,
        }

    # Month start dates: May to October 2026
    months = [
        date(2026, 5, 1),
        date(2026, 6, 1),
        date(2026, 7, 1),
        date(2026, 8, 1),
        date(2026, 9, 1),
        date(2026, 10, 1),
    ]

    # --- SCENARIO 1: Same merchant under two descriptors (StreamPulse) ---
    m1 = SCENARIO_MERCHANTS["scenario_1_dual_descriptor"]
    for i, m_start in enumerate(months):
        d = date(m_start.year, m_start.month, 5)
        desc = m1.descriptors[i % 2]  # alternate descriptors
        transactions.append(make_txn(d, desc, m1.default_amount, m1.default_channel, "scenario_1_dual_descriptor", norm_desc="StreamPulse Entertainment"))

    # --- SCENARIO 2: Monthly subscription with silent price increase (CloudDesk Pro) ---
    m2 = SCENARIO_MERCHANTS["scenario_2_price_increase"]
    for i, m_start in enumerate(months):
        d = date(m_start.year, m_start.month, 12)
        amount = 799.00 if i < 3 else 999.00  # price hike after 3 months
        transactions.append(make_txn(d, m2.descriptors[0], amount, m2.default_channel, "scenario_2_price_increase", norm_desc="CloudDesk Pro"))

    # --- SCENARIO 3: Free trial followed by paid conversion (SynthWrite AI) ---
    m3 = SCENARIO_MERCHANTS["scenario_3_trial_conversion"]
    # Day 0 trial authorization / 0 charge
    transactions.append(make_txn(date(2026, 5, 10), m3.descriptors[0], 0.00, m3.default_channel, "scenario_3_trial_conversion", norm_desc="SynthWrite AI"))
    # Converted paid debits: Day 14 (May 24) and subsequent 24th of each month
    for m_start in months:
        d = date(m_start.year, m_start.month, 24)
        transactions.append(make_txn(d, m3.descriptors[1], m3.default_amount, m3.default_channel, "scenario_3_trial_conversion", norm_desc="SynthWrite AI"))

    # --- SCENARIO 4: Membership with no recorded usage (Zenith Fitness Club) ---
    m4 = SCENARIO_MERCHANTS["scenario_4_unused_membership"]
    for m_start in months:
        d = date(m_start.year, m_start.month, 1)
        transactions.append(make_txn(d, m4.descriptors[0], m4.default_amount, m4.default_channel, "scenario_4_unused_membership", norm_desc="Zenith Fitness Club"))

    # --- SCENARIO 5: Successful charge after user cancellation (SkyVault Backup) ---
    m5 = SCENARIO_MERCHANTS["scenario_5_post_cancel_charge"]
    # Charged in May, June, July
    for m_start in months[:3]:
        d = date(m_start.year, m_start.month, 15)
        transactions.append(make_txn(d, m5.descriptors[0], m5.default_amount, m5.default_channel, "scenario_5_post_cancel_charge", norm_desc="SkyVault Backup"))
    # Cancellation happened on 2026-07-20 (in notifications).
    # Month 4 (August) charge observed despite cancellation:
    transactions.append(make_txn(date(2026, 8, 15), m5.descriptors[0], m5.default_amount, m5.default_channel, "scenario_5_post_cancel_charge", norm_desc="SkyVault Backup"))

    # --- SCENARIO 6: Annual insurance premium (Suraksha General Insurance) ---
    m6 = SCENARIO_MERCHANTS["scenario_6_annual_insurance"]
    transactions.append(make_txn(date(2026, 5, 18), m6.descriptors[0], m6.default_amount, m6.default_channel, "scenario_6_annual_insurance", norm_desc="Suraksha General Insurance"))

    # --- SCENARIO 7: Variable monthly utility bill (FiberNet Broadband) ---
    m7 = SCENARIO_MERCHANTS["scenario_7_variable_utility"]
    variable_amounts = [1420.00, 1850.00, 1290.00, 2100.00, 1630.00, 1780.00]
    for i, m_start in enumerate(months):
        d = date(m_start.year, m_start.month, 8)
        transactions.append(make_txn(d, m7.descriptors[0], variable_amounts[i], m7.default_channel, "scenario_7_variable_utility", norm_desc="FiberNet Broadband"))

    # --- SCENARIO 8: Two subscriptions in same category (CineFlow & IndieWatch) ---
    m8a = SCENARIO_MERCHANTS["scenario_8_category_overlap_a"]
    m8b = SCENARIO_MERCHANTS["scenario_8_category_overlap_b"]
    for m_start in months:
        d_a = date(m_start.year, m_start.month, 10)
        transactions.append(make_txn(d_a, m8a.descriptors[0], m8a.default_amount, m8a.default_channel, "scenario_8_category_overlap_a", norm_desc="CineFlow Premium"))
        d_b = date(m_start.year, m_start.month, 18)
        transactions.append(make_txn(d_b, m8b.descriptors[0], m8b.default_amount, m8b.default_channel, "scenario_8_category_overlap_b", norm_desc="IndieWatch Movies"))

    # --- SCENARIO 9: UPI AutoPay with max amount higher than usual debit (QuickCab) ---
    m9 = SCENARIO_MERCHANTS["scenario_9_autopay_high_limit"]
    for m_start in months:
        d = date(m_start.year, m_start.month, 2)
        transactions.append(make_txn(d, m9.descriptors[0], m9.default_amount, m9.default_channel, "scenario_9_autopay_high_limit", norm_desc="QuickCab Monthly Pass"))

    # --- SCENARIO 10: Irregular recurring merchant payment (AquaPure Springs) ---
    m10 = SCENARIO_MERCHANTS["scenario_10_irregular_recurring"]
    irregular_dates = [
        date(2026, 5, 4),
        date(2026, 5, 29),
        date(2026, 6, 25),
        date(2026, 7, 20),
        date(2026, 8, 16),
        date(2026, 9, 12),
        date(2026, 10, 8),
    ]
    for d in irregular_dates:
        transactions.append(make_txn(d, m10.descriptors[0], m10.default_amount, m10.default_channel, "scenario_10_irregular_recurring", norm_desc="AquaPure Springs"))

    # --- SCENARIO 11: Card recurring mandate (DevStack Cloud Hosting) ---
    m11 = SCENARIO_MERCHANTS["scenario_11_card_mandate"]
    for m_start in months:
        d = date(m_start.year, m_start.month, 3)
        transactions.append(make_txn(d, m11.descriptors[0], m11.default_amount, m11.default_channel, "scenario_11_card_mandate", norm_desc="DevStack Cloud Hosting"))

    # --- SCENARIO 12: Unknown / Ambiguous merchant routed to manual review ---
    m12 = SCENARIO_MERCHANTS["scenario_12_ambiguous_manual_review"]
    for m_start in months:
        d = date(m_start.year, m_start.month, 14)
        transactions.append(make_txn(d, m12.descriptors[0], m12.default_amount, m12.default_channel, "scenario_12_ambiguous_manual_review", norm_desc="Unidentified Aggregator Gateway"))

    # --- Monthly Salary Credits ---
    for m_start in months:
        # Last day of month
        if m_start.month in (5, 7, 8, 10):
            d = date(m_start.year, m_start.month, 31)
        elif m_start.month in (6, 9):
            d = date(m_start.year, m_start.month, 30)
        transactions.append(make_txn(d, "ACH/SYNTHETIC TECH LABS/SALARY", 125000.00, "bank_transfer", "salary_credit", direction="credit", norm_desc="Synthetic Tech Labs Salary"))

    # --- One-off transactions (realistic everyday living expenses) ---
    for m_start in months:
        for _ in range(7):  # ~42 one-off transactions across 6 months
            day = rng.randint(1, 28)
            d = date(m_start.year, m_start.month, day)
            merchant = rng.choice(ONE_OFF_MERCHANTS)
            desc = rng.choice(merchant.descriptors)
            # Add slight variance (+/- 15%)
            jitter = rng.uniform(0.85, 1.15)
            amt = round(merchant.default_amount * jitter, 2)
            transactions.append(make_txn(d, desc, amt, merchant.default_channel, "one_off", norm_desc=merchant.canonical_name))

    # Sort deterministically by date and external_synthetic_id
    transactions.sort(key=lambda t: (t["transaction_date"], t["external_synthetic_id"]))
    return transactions

