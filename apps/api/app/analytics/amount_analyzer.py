"""Amount analyzer for calculating representative amount and variance patterns."""
import statistics
from dataclasses import dataclass
from decimal import Decimal
from typing import List
from app.analytics.config import FIXED_AMOUNT_CV_THRESHOLD


@dataclass
class AmountAnalysis:
    """Statistical summary of transaction amounts for a recurring commitment."""
    count: int
    representative_amount: Decimal
    amount_min: Decimal
    amount_max: Decimal
    amount_pattern: str  # fixed, variable, insufficient_data
    mean_amount: float = 0.0
    std_dev_amount: float = 0.0
    cv: float = 0.0
    has_price_change: bool = False


def analyze_amounts(amounts: List[Decimal]) -> AmountAnalysis:
    """Analyze transaction amounts to determine representative value and variance pattern.
    
    Args:
        amounts: List of Decimal values for transactions.
        
    Returns:
        AmountAnalysis dataclass with median, min, max, and pattern classification.
    """
    count = len(amounts)
    if count == 0:
        zero = Decimal("0.00")
        return AmountAnalysis(
            count=0,
            representative_amount=zero,
            amount_min=zero,
            amount_max=zero,
            amount_pattern="insufficient_data",
        )

    float_amounts = [float(a) for a in amounts]
    min_dec = min(amounts)
    max_dec = max(amounts)
    median_val = Decimal(str(round(statistics.median(float_amounts), 2)))
    has_change = min_dec != max_dec

    if count == 1:
        return AmountAnalysis(
            count=1,
            representative_amount=amounts[0],
            amount_min=amounts[0],
            amount_max=amounts[0],
            amount_pattern="insufficient_data",
            mean_amount=float_amounts[0],
            std_dev_amount=0.0,
            cv=0.0,
            has_price_change=False,
        )

    mean_val = statistics.mean(float_amounts)
    stdev_val = statistics.stdev(float_amounts) if count >= 2 else 0.0
    cv = (stdev_val / mean_val) if mean_val > 0 else 0.0

    if not has_change or cv <= FIXED_AMOUNT_CV_THRESHOLD:
        pattern = "fixed"
    else:
        pattern = "variable"

    return AmountAnalysis(
        count=count,
        representative_amount=median_val,
        amount_min=min_dec,
        amount_max=max_dec,
        amount_pattern=pattern,
        mean_amount=round(mean_val, 2),
        std_dev_amount=round(stdev_val, 2),
        cv=round(cv, 4),
        has_price_change=has_change,
    )
