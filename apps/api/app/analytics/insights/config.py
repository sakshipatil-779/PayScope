"""Configuration constants and thresholds for Phase 6 insight and anomaly detection."""
from dataclasses import dataclass


@dataclass(frozen=True)
class PriceChangeThresholds:
    """Thresholds for sustained price increase detection."""
    min_previous_regime_charges: int = 2
    min_new_regime_charges: int = 2
    min_percentage_increase: float = 5.0  # 5% or greater
    max_regime_cv: float = 0.05           # Each regime must have stable amounts (CV <= 5%)


@dataclass(frozen=True)
class UsageAnalysisThresholds:
    """Thresholds for service usage and inactivity analysis."""
    min_observation_window_days: int = 90
    inactivity_threshold_days: int = 90


@dataclass(frozen=True)
class UnusualAmountThresholds:
    """Thresholds for isolated unusual debit detection."""
    fixed_cadence_multiplier: float = 1.50   # 50% above representative amount
    utility_outlier_multiplier: float = 2.50  # 150% above utility median


INSIGHT_DETECTOR_VERSION: str = "v1.0"
DETECTOR_VERSION: str = INSIGHT_DETECTOR_VERSION
