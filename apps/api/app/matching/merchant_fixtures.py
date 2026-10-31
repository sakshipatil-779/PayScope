"""Curated merchant reference fixtures and known descriptor aliases."""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class AliasFixture:
    """Descriptor alias definition for initial database seeding."""

    alias_text: str
    matcher_type: str = "exact"  # exact, prefix, regex, token_pattern
    pattern: Optional[str] = None
    confidence_band: str = "high"
    reference_source: str = "curated_demo_fixtures"


@dataclass(frozen=True)
class CanonicalMerchantFixture:
    """Canonical merchant definition for reference registry."""

    canonical_name: str
    category: str
    commitment_type_default: Optional[str] = None
    website_url: Optional[str] = None
    support_url: Optional[str] = None
    is_fictional: bool = True
    aliases: List[AliasFixture] = field(default_factory=list)


CANONICAL_MERCHANT_REGISTRY: List[CanonicalMerchantFixture] = [
    # 1. StreamPulse Entertainment (Scenario 1)
    CanonicalMerchantFixture(
        canonical_name="StreamPulse Entertainment",
        category="entertainment",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("UPI/STREAMPULSE/BILLPAY/982138", matcher_type="exact"),
            AliasFixture("POS STRMPLSE INTL BLR", matcher_type="exact"),
            AliasFixture("streampulse", matcher_type="token_pattern"),
            AliasFixture("strmplse", matcher_type="token_pattern"),
        ],
    ),
    # 2. CloudDesk Pro (Scenario 2)
    CanonicalMerchantFixture(
        canonical_name="CloudDesk Pro",
        category="cloud_software",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("RAZORPAY*CLOUDDESK BLR", matcher_type="exact"),
            AliasFixture("CLOUDDESK PRO SUBSCRIPTION", matcher_type="exact"),
            AliasFixture("clouddesk", matcher_type="token_pattern"),
        ],
    ),
    # 3. SynthWrite AI (Scenario 3)
    CanonicalMerchantFixture(
        canonical_name="SynthWrite AI",
        category="productivity",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("UPI/SYNTHWRITE/AUTOPAY/88129", matcher_type="exact"),
            AliasFixture("SYNTHWRITE AI PRO PLAN", matcher_type="exact"),
            AliasFixture("synthwrite", matcher_type="token_pattern"),
        ],
    ),
    # 4. Zenith Fitness Club (Scenario 4)
    CanonicalMerchantFixture(
        canonical_name="Zenith Fitness Club",
        category="health_fitness",
        commitment_type_default="membership",
        aliases=[
            AliasFixture("ZENITH FITNESS BLR CLUB MEM", matcher_type="exact"),
            AliasFixture("POS ZENITH FITNESS INDIRANAGAR", matcher_type="exact"),
            AliasFixture("zenith fitness", matcher_type="prefix"),
        ],
    ),
    # 5. SkyVault Backup (Scenario 5)
    CanonicalMerchantFixture(
        canonical_name="SkyVault Backup",
        category="cloud_software",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("SKYVAULT STORAGE MUMBAI", matcher_type="exact"),
            AliasFixture("UPI/SKYVAULT/MONTHLY", matcher_type="exact"),
            AliasFixture("skyvault", matcher_type="token_pattern"),
        ],
    ),
    # 6. Suraksha General Insurance (Scenario 6)
    CanonicalMerchantFixture(
        canonical_name="Suraksha General Insurance",
        category="insurance",
        commitment_type_default="insurance",
        aliases=[
            AliasFixture("ACH/SURAKSHA GEN INS/ANNUAL", matcher_type="exact"),
            AliasFixture("SURAKSHA INSURANCE PREMIUM", matcher_type="exact"),
            AliasFixture("suraksha", matcher_type="prefix"),
        ],
    ),
    # 7. FiberNet Broadband (Scenario 7)
    CanonicalMerchantFixture(
        canonical_name="FiberNet Broadband",
        category="utilities",
        commitment_type_default="utility_bill",
        aliases=[
            AliasFixture("FIBERNET BROADBAND BILLPAY", matcher_type="exact"),
            AliasFixture("UPI/FIBERNET/UTILITY", matcher_type="exact"),
            AliasFixture("fibernet", matcher_type="prefix"),
        ],
    ),
    # 8a. CineFlow Premium (Scenario 8a)
    CanonicalMerchantFixture(
        canonical_name="CineFlow Premium",
        category="entertainment",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("CINEFLOW OTT STREAMING", matcher_type="exact"),
            AliasFixture("UPI/CINEFLOW/MTHLY", matcher_type="exact"),
            AliasFixture("cineflow", matcher_type="prefix"),
        ],
    ),
    # 8b. IndieWatch Movies (Scenario 8b)
    CanonicalMerchantFixture(
        canonical_name="IndieWatch Movies",
        category="entertainment",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("INDIEWATCH MOVIES IND", matcher_type="exact"),
            AliasFixture("UPI/INDIEWATCH/STREAM", matcher_type="exact"),
            AliasFixture("indiewatch", matcher_type="prefix"),
        ],
    ),
    # 9. QuickCab Monthly Pass (Scenario 9)
    CanonicalMerchantFixture(
        canonical_name="QuickCab Monthly Pass",
        category="transportation",
        commitment_type_default="recurring_pass",
        aliases=[
            AliasFixture("UPI/QUICKCAB/AUTOPAY/PASS", matcher_type="exact"),
            AliasFixture("QUICKCAB COMMUTE PASS", matcher_type="exact"),
            AliasFixture("quickcab", matcher_type="token_pattern"),
        ],
    ),
    # 10. AquaPure Springs (Scenario 10)
    CanonicalMerchantFixture(
        canonical_name="AquaPure Springs",
        category="utilities",
        commitment_type_default="recurring_delivery",
        aliases=[
            AliasFixture("AQUAPURE SPRING WATER BLR", matcher_type="exact"),
            AliasFixture("UPI/AQUAPURE/DELIVERY", matcher_type="exact"),
            AliasFixture("aquapure", matcher_type="token_pattern"),
        ],
    ),
    # 11. DevStack Cloud Hosting (Scenario 11)
    CanonicalMerchantFixture(
        canonical_name="DevStack Cloud Hosting",
        category="cloud_software",
        commitment_type_default="subscription",
        aliases=[
            AliasFixture("E-MANDATE IN*DEVSTACK CLOUD MUMBAI", matcher_type="exact"),
            AliasFixture("DEVSTACK HOSTING CC", matcher_type="exact"),
            AliasFixture("devstack", matcher_type="token_pattern"),
        ],
    ),
    # --- One-off Merchants ---
    CanonicalMerchantFixture(
        canonical_name="FoodSwift Bangalore",
        category="food_dining",
        aliases=[
            AliasFixture("UPI/FOODSWIFT/ORDER", matcher_type="exact"),
            AliasFixture("FOODSWIFT BLR", matcher_type="exact"),
            AliasFixture("foodswift", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="DailyBites Delivery",
        category="food_dining",
        aliases=[
            AliasFixture("DAILYBITES FOOD APP", matcher_type="exact"),
            AliasFixture("UPI/DAILYBITES/PAY", matcher_type="exact"),
            AliasFixture("dailybites", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="FreshMart Hypermarket",
        category="groceries",
        aliases=[
            AliasFixture("POS FRESHMART KORAMANGALA", matcher_type="exact"),
            AliasFixture("FRESHMART RETAIL BLR", matcher_type="exact"),
            AliasFixture("freshmart", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="OrganicBazaar Indiranagar",
        category="groceries",
        aliases=[
            AliasFixture("ORGANIC BAZAAR INDIRANAGAR", matcher_type="exact"),
            AliasFixture("UPI/ORGANICBAZAAR", matcher_type="exact"),
            AliasFixture("organicbazaar", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="BeanRoast Artisan Cafe",
        category="food_dining",
        aliases=[
            AliasFixture("BEANROAST CAFE INDIRANAGAR", matcher_type="exact"),
            AliasFixture("POS BEANROAST", matcher_type="exact"),
            AliasFixture("beanroast", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="National Petroleum Pump",
        category="transportation",
        aliases=[
            AliasFixture("POS NATL PETROL BSK II", matcher_type="exact"),
            AliasFixture("HPCL RETAIL OUTLET", matcher_type="exact"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="CityCab Trips",
        category="transportation",
        aliases=[
            AliasFixture("UPI/CITYCAB/RIDE", matcher_type="exact"),
            AliasFixture("CITYCAB MOBILITY SERVICES", matcher_type="exact"),
            AliasFixture("citycab", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="MedPlus Synthetic Chemist",
        category="health_fitness",
        aliases=[
            AliasFixture("MEDPLUS PHARMACY IND", matcher_type="exact"),
            AliasFixture("POS MEDPLUS BLR", matcher_type="exact"),
            AliasFixture("medplus", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="Amazon Synthetic Retail",
        category="shopping",
        aliases=[
            AliasFixture("AMAZON SELLER SERVICES BLR", matcher_type="exact"),
            AliasFixture("AMZN RETAIL INDIA", matcher_type="exact"),
            AliasFixture("amazon", matcher_type="token_pattern"),
        ],
    ),
    CanonicalMerchantFixture(
        canonical_name="Synthetic Tech Labs Salary",
        category="finance_loan",
        aliases=[
            AliasFixture("ACH/SYNTHETIC TECH LABS/SALARY", matcher_type="exact"),
        ],
    ),
]
