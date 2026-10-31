"""Tests for synthetic data generation reproducibility and scenario coverage."""
from app.generators.config import GeneratorConfig
from app.generators.dataset_generator import DatasetGenerator


def test_generator_determinism():
    """Verify that using the same seed produces identical datasets."""
    gen1 = DatasetGenerator(GeneratorConfig(seed=42))
    dataset1 = gen1.generate()

    gen2 = DatasetGenerator(GeneratorConfig(seed=42))
    dataset2 = gen2.generate()

    assert len(dataset1["transactions"]) == len(dataset2["transactions"])
    assert len(dataset1["notifications"]) == len(dataset2["notifications"])

    # First transaction identical
    assert dataset1["transactions"][0]["external_synthetic_id"] == dataset2["transactions"][0]["external_synthetic_id"]
    assert dataset1["transactions"][0]["amount"] == dataset2["transactions"][0]["amount"]

    # Manifest identical
    assert dataset1["manifest"]["summary"] == dataset2["manifest"]["summary"]


def test_scenario_coverage_and_thresholds():
    """Verify all 12 scenarios are present, and minimum thresholds (80+ txns, 15+ notifs) are met."""
    config = GeneratorConfig(seed=42)
    generator = DatasetGenerator(config)
    dataset = generator.generate()

    transactions = dataset["transactions"]
    notifications = dataset["notifications"]
    manifest = dataset["manifest"]

    assert len(transactions) >= 80, f"Expected at least 80 transactions, got {len(transactions)}"
    assert len(notifications) >= 15, f"Expected at least 15 notifications, got {len(notifications)}"

    # Check scenario coverage
    txn_scenarios = set(t.get("scenario_key") for t in transactions if t.get("scenario_key"))
    required_txn_scenarios = {
        "scenario_1_dual_descriptor",
        "scenario_2_price_increase",
        "scenario_3_trial_conversion",
        "scenario_4_unused_membership",
        "scenario_5_post_cancel_charge",
        "scenario_6_annual_insurance",
        "scenario_7_variable_utility",
        "scenario_8_category_overlap_a",
        "scenario_8_category_overlap_b",
        "scenario_9_autopay_high_limit",
        "scenario_10_irregular_recurring",
        "scenario_11_card_mandate",
        "scenario_12_ambiguous_manual_review",
    }
    missing = required_txn_scenarios - txn_scenarios
    assert not missing, f"Missing required scenarios: {missing}"

    # Verify notification event types
    event_types = set(n["event_type"] for n in notifications)
    assert "mandate_created" in event_types
    assert "payment_success" in event_types
    assert "price_changed" in event_types
    assert "trial_started" in event_types
    assert "subscription_cancelled" in event_types


def test_transaction_fields_and_synthetic_provenance():
    """Verify all generated transactions have synthetic flags, references, and positive amounts."""
    config = GeneratorConfig(seed=42)
    generator = DatasetGenerator(config)
    dataset = generator.generate()

    for txn in dataset["transactions"]:
        assert txn["is_synthetic"] is True
        assert txn["external_synthetic_id"].startswith("SYN-TXN-")
        assert txn["payment_reference"].startswith("SYNREF")
        assert txn["amount"] >= 0.0
        assert txn["currency"] == "INR"
        assert txn["transaction_status"] == "successful"
        assert len(txn["raw_descriptor"]) > 0
