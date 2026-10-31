"""Fictional merchant fixtures and scenario definitions for synthetic generation."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class MerchantFixture:
    """Fictional demo merchant definition with raw descriptor templates."""

    canonical_name: str
    category: str
    descriptors: List[str]
    default_channel: str
    default_amount: float
    cadence: str  # monthly, annual, irregular, one_off
    is_fictional: bool = True
    notes: Optional[str] = None


SCENARIO_MERCHANTS = {
    # 1. Same canonical merchant under two descriptors
    "scenario_1_dual_descriptor": MerchantFixture(
        canonical_name="StreamPulse Entertainment",
        category="entertainment",
        descriptors=[
            "UPI/STREAMPULSE/BILLPAY/982138",
            "POS STRMPLSE INTL BLR",
        ],
        default_channel="upi",
        default_amount=499.00,
        cadence="monthly",
        notes="Same streaming merchant billing across alternate UPI and card POS descriptors.",
    ),
    # 2. Monthly subscription with a silent price increase
    "scenario_2_price_increase": MerchantFixture(
        canonical_name="CloudDesk Pro",
        category="cloud_software",
        descriptors=[
            "RAZORPAY*CLOUDDESK BLR",
            "CLOUDDESK PRO SUBSCRIPTION",
        ],
        default_channel="card",
        default_amount=799.00,  # increases to 999.00
        cadence="monthly",
        notes="Silent price hike from ₹799 to ₹999 after 3 months.",
    ),
    # 3. Free trial followed by paid conversion
    "scenario_3_trial_conversion": MerchantFixture(
        canonical_name="SynthWrite AI",
        category="productivity",
        descriptors=[
            "UPI/SYNTHWRITE/AUTOPAY/88129",
            "SYNTHWRITE AI PRO PLAN",
        ],
        default_channel="upi",
        default_amount=1299.00,
        cadence="monthly",
        notes="14-day zero-cost trial followed by recurring ₹1,299 debits.",
    ),
    # 4. Membership with no recorded usage during covered period
    "scenario_4_unused_membership": MerchantFixture(
        canonical_name="Zenith Fitness Club",
        category="health_fitness",
        descriptors=[
            "ZENITH FITNESS BLR CLUB MEM",
            "POS ZENITH FITNESS INDIRANAGAR",
        ],
        default_channel="card",
        default_amount=2499.00,
        cadence="monthly",
        notes="Ongoing gym membership with zero recorded usage access events.",
    ),
    # 5. Successful charge after user-confirmed cancellation
    "scenario_5_post_cancel_charge": MerchantFixture(
        canonical_name="SkyVault Backup",
        category="cloud_software",
        descriptors=[
            "SKYVAULT STORAGE MUMBAI",
            "UPI/SKYVAULT/MONTHLY",
        ],
        default_channel="card",
        default_amount=349.00,
        cadence="monthly",
        notes="Cancellation recorded in month 3, yet charged again in month 4.",
    ),
    # 6. Annual insurance premium
    "scenario_6_annual_insurance": MerchantFixture(
        canonical_name="Suraksha General Insurance",
        category="insurance",
        descriptors=[
            "ACH/SURAKSHA GEN INS/ANNUAL",
            "SURAKSHA INSURANCE PREMIUM",
        ],
        default_channel="bank_transfer",
        default_amount=14500.00,
        cadence="annual",
        notes="High-value annual health insurance renewal.",
    ),
    # 7. Variable monthly utility bill
    "scenario_7_variable_utility": MerchantFixture(
        canonical_name="FiberNet Broadband",
        category="utilities",
        descriptors=[
            "FIBERNET BROADBAND BILLPAY",
            "UPI/FIBERNET/UTILITY",
        ],
        default_channel="upi",
        default_amount=1499.00,
        cadence="monthly",
        notes="Broadband utility bill with variable monthly usage add-ons.",
    ),
    # 8. Two subscriptions in same category
    "scenario_8_category_overlap_a": MerchantFixture(
        canonical_name="CineFlow Premium",
        category="entertainment",
        descriptors=[
            "CINEFLOW OTT STREAMING",
            "UPI/CINEFLOW/MTHLY",
        ],
        default_channel="upi",
        default_amount=649.00,
        cadence="monthly",
        notes="Primary OTT video subscription.",
    ),
    "scenario_8_category_overlap_b": MerchantFixture(
        canonical_name="IndieWatch Movies",
        category="entertainment",
        descriptors=[
            "INDIEWATCH MOVIES IND",
            "UPI/INDIEWATCH/STREAM",
        ],
        default_channel="upi",
        default_amount=299.00,
        cadence="monthly",
        notes="Secondary niche movie subscription in same category.",
    ),
    # 9. UPI AutoPay with max amount higher than usual debit
    "scenario_9_autopay_high_limit": MerchantFixture(
        canonical_name="QuickCab Monthly Pass",
        category="transportation",
        descriptors=[
            "UPI/QUICKCAB/AUTOPAY/PASS",
            "QUICKCAB COMMUTE PASS",
        ],
        default_channel="upi",
        default_amount=1999.00,
        cadence="monthly",
        notes="UPI AutoPay mandate with max limit ₹5,000, recurring debit ₹1,999.",
    ),
    # 10. Irregular recurring merchant payment
    "scenario_10_irregular_recurring": MerchantFixture(
        canonical_name="AquaPure Springs",
        category="utilities",
        descriptors=[
            "AQUAPURE SPRING WATER BLR",
            "UPI/AQUAPURE/DELIVERY",
        ],
        default_channel="upi",
        default_amount=650.00,
        cadence="irregular",
        notes="Packaged water refills ordered every 20-35 days.",
    ),
    # 11. Card recurring mandate
    "scenario_11_card_mandate": MerchantFixture(
        canonical_name="DevStack Cloud Hosting",
        category="cloud_software",
        descriptors=[
            "E-MANDATE IN*DEVSTACK CLOUD MUMBAI",
            "DEVSTACK HOSTING CC",
        ],
        default_channel="card",
        default_amount=3499.00,
        cadence="monthly",
        notes="Standing e-mandate on credit card for developer infrastructure.",
    ),
    # 12. Unknown/ambiguous merchant routed to manual review
    "scenario_12_ambiguous_manual_review": MerchantFixture(
        canonical_name="Unidentified Aggregator Gateway",
        category="other",
        descriptors=[
            "BILLDESK*PG-MUMBAI-TXN99281",
            "RAZORPAY*MERCH_INTL_4819",
        ],
        default_channel="upi",
        default_amount=850.00,
        cadence="monthly",
        notes="Ambiguous gateway charge requiring user manual review.",
    ),
}

ONE_OFF_MERCHANTS: List[MerchantFixture] = [
    MerchantFixture("FoodSwift Bangalore", "food_dining", ["UPI/FOODSWIFT/ORDER", "FOODSWIFT BLR"], "upi", 340.0, "one_off"),
    MerchantFixture("DailyBites Delivery", "food_dining", ["DAILYBITES FOOD APP", "UPI/DAILYBITES/PAY"], "upi", 480.0, "one_off"),
    MerchantFixture("FreshMart Hypermarket", "groceries", ["POS FRESHMART KORAMANGALA", "FRESHMART RETAIL BLR"], "card", 2150.0, "one_off"),
    MerchantFixture("OrganicBazaar Indiranagar", "groceries", ["ORGANIC BAZAAR INDIRANAGAR", "UPI/ORGANICBAZAAR"], "upi", 890.0, "one_off"),
    MerchantFixture("BeanRoast Artisan Cafe", "food_dining", ["BEANROAST CAFE INDIRANAGAR", "POS BEANROAST"], "card", 420.0, "one_off"),
    MerchantFixture("National Petroleum Pump", "transportation", ["POS NATL PETROL BSK II", "HPCL RETAIL OUTLET"], "card", 1500.0, "one_off"),
    MerchantFixture("CityCab Trips", "transportation", ["UPI/CITYCAB/RIDE", "CITYCAB MOBILITY SERVICES"], "upi", 220.0, "one_off"),
    MerchantFixture("MedPlus Synthetic Chemist", "health_fitness", ["MEDPLUS PHARMACY IND", "POS MEDPLUS BLR"], "card", 560.0, "one_off"),
    MerchantFixture("Amazon Synthetic Retail", "shopping", ["AMAZON SELLER SERVICES BLR", "AMZN RETAIL INDIA"], "card", 1899.0, "one_off"),
]
