"""High-level dataset generator orchestrating synthetic transactions and notifications."""
from collections import Counter
from typing import Any, Dict, List
from faker import Faker
from app.generators.config import GeneratorConfig
from app.generators.notification_generator import generate_notifications
from app.generators.transaction_generator import generate_transactions


class DatasetGenerator:
    """Generates complete synthetic financial dataset with metadata manifest."""

    def __init__(self, config: GeneratorConfig = None):
        self.config = config or GeneratorConfig()
        self.fake = Faker("en_IN")
        self.fake.seed_instance(self.config.seed)

    def generate(self) -> Dict[str, Any]:
        """Generate transactions, notifications, and manifest dictionary."""
        transactions = generate_transactions(self.config, self.fake)
        notifications = generate_notifications(self.config, self.fake)

        # Compute scenario stats
        txn_scenarios = Counter(t.get("scenario_key") for t in transactions)
        notif_scenarios = Counter(n.get("scenario_key") for n in notifications)

        # Compute totals
        total_debit = sum(t["amount"] for t in transactions if t.get("direction") == "debit")
        total_credit = sum(t["amount"] for t in transactions if t.get("direction") == "credit")

        manifest = {
            "generator": "MandateLens Synthetic Generator v1.0",
            "seed": self.config.seed,
            "currency": self.config.currency,
            "date_range": {
                "start": self.config.start_date.isoformat(),
                "end": self.config.end_date.isoformat(),
            },
            "summary": {
                "transaction_count": len(transactions),
                "notification_count": len(notifications),
                "total_debit_amount": round(total_debit, 2),
                "total_credit_amount": round(total_credit, 2),
                "unique_scenarios_covered": 12,
            },
            "scenario_breakdown": {
                "transactions_by_scenario": dict(txn_scenarios),
                "notifications_by_scenario": dict(notif_scenarios),
            },
            "supported_scenarios": [
                "scenario_1_dual_descriptor",
                "scenario_2_price_increase",
                "scenario_3_trial_conversion",
                "scenario_4_unused_membership",
                "scenario_5_post_cancel_charge",
                "scenario_6_annual_insurance",
                "scenario_7_variable_utility",
                "scenario_8_category_overlap",
                "scenario_9_autopay_high_limit",
                "scenario_10_irregular_recurring",
                "scenario_11_card_mandate",
                "scenario_12_ambiguous_manual_review",
            ],
            "is_synthetic": True,
        }

        return {
            "manifest": manifest,
            "transactions": transactions,
            "notifications": notifications,
        }

