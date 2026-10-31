"""Configuration constants and tolerances for the cadence discovery engine."""
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CadenceIntervalBounds:
    """Day interval boundaries for different payment cadences."""
    weekly: Tuple[int, int] = (6, 8)
    fortnightly: Tuple[int, int] = (12, 16)
    monthly_days: Tuple[int, int] = (28, 31)
    quarterly_days: Tuple[int, int] = (80, 100)
    annual_days: Tuple[int, int] = (350, 380)
    irregular_days: Tuple[int, int] = (20, 35)


# Amount coefficient of variation threshold below which amount is considered fixed
FIXED_AMOUNT_CV_THRESHOLD: float = 0.05

# Minimum events required to declare an annual commitment recurring
MIN_ANNUAL_EVENTS_FOR_CONFIRMED: int = 2

# Minimum events required to classify as irregular cadence
MIN_IRREGULAR_EVENTS: int = 4

# Minimum events required for weekly/fortnightly/monthly/quarterly
MIN_RECURRING_EVENTS: int = 2

# Confidence scoring weights
CONFIDENCE_WEIGHT_COUNT_GE_6: float = 30.0
CONFIDENCE_WEIGHT_COUNT_4_5: float = 25.0
CONFIDENCE_WEIGHT_COUNT_3: float = 20.0
CONFIDENCE_WEIGHT_COUNT_2: float = 10.0
CONFIDENCE_WEIGHT_COUNT_1: float = 0.0

CONFIDENCE_WEIGHT_INTERVAL_CONSISTENT: float = 25.0   # std_dev <= 2 days
CONFIDENCE_WEIGHT_INTERVAL_MODERATE: float = 15.0     # std_dev <= 5 days
CONFIDENCE_WEIGHT_INTERVAL_IRREGULAR: float = 5.0

CONFIDENCE_WEIGHT_AMOUNT_FIXED: float = 20.0
CONFIDENCE_WEIGHT_AMOUNT_VARIABLE: float = 10.0

CONFIDENCE_WEIGHT_MERCHANT_HIGH: float = 20.0
CONFIDENCE_WEIGHT_MERCHANT_MEDIUM: float = 10.0
CONFIDENCE_WEIGHT_MERCHANT_UNRESOLVED: float = 5.0

CONFIDENCE_WEIGHT_RECURRING_CHANNEL: float = 5.0

# Confidence Band Thresholds
BAND_HIGH_THRESHOLD: float = 75.0
BAND_MEDIUM_THRESHOLD: float = 45.0

# Detection version
DETECTOR_VERSION: str = "v1.0"
