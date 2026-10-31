"""Confidence scoring, band assignment, and explanation generation for commitments."""
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Set
from app.analytics.amount_analyzer import AmountAnalysis
from app.analytics.cadence_classifier import CadenceClassification
from app.analytics.config import (
    BAND_HIGH_THRESHOLD,
    BAND_MEDIUM_THRESHOLD,
    CONFIDENCE_WEIGHT_AMOUNT_FIXED,
    CONFIDENCE_WEIGHT_AMOUNT_VARIABLE,
    CONFIDENCE_WEIGHT_COUNT_1,
    CONFIDENCE_WEIGHT_COUNT_2,
    CONFIDENCE_WEIGHT_COUNT_3,
    CONFIDENCE_WEIGHT_COUNT_4_5,
    CONFIDENCE_WEIGHT_COUNT_GE_6,
    CONFIDENCE_WEIGHT_INTERVAL_CONSISTENT,
    CONFIDENCE_WEIGHT_INTERVAL_IRREGULAR,
    CONFIDENCE_WEIGHT_INTERVAL_MODERATE,
    CONFIDENCE_WEIGHT_MERCHANT_HIGH,
    CONFIDENCE_WEIGHT_MERCHANT_MEDIUM,
    CONFIDENCE_WEIGHT_MERCHANT_UNRESOLVED,
    CONFIDENCE_WEIGHT_RECURRING_CHANNEL,
)
from app.analytics.interval_analyzer import IntervalAnalysis


@dataclass
class ConfidenceAssessment:
    """Output of confidence evaluation."""
    score: Decimal
    band: str  # high, medium, low, needs_review
    reason_codes: List[str]
    explanation: str


def calculate_confidence(
    cadence_res: CadenceClassification,
    interval_info: IntervalAnalysis,
    amount_info: AmountAnalysis,
    merchant_match_confidence: Optional[str] = None,
    is_merchant_resolved: bool = True,
    payment_channels: Optional[Set[str]] = None,
    display_name: str = "Unknown",
) -> ConfidenceAssessment:
    """Evaluate confidence score, band, codes and explanation for recurring detection.
    
    Args:
        cadence_res: Cadence classification result.
        interval_info: Interval statistics.
        amount_info: Amount statistics.
        merchant_match_confidence: Confidence from merchant resolver ('high', 'medium', etc.).
        is_merchant_resolved: True if matched to a canonical merchant.
        payment_channels: Set of payment channels observed in the stream.
        display_name: Name of merchant/obligation.
        
    Returns:
        ConfidenceAssessment with score (0-100), band, codes and explanation.
    """
    score = 0.0
    reason_codes: List[str] = []
    explanation_parts: List[str] = []

    count = interval_info.count

    # 1. Occurrence count scoring
    if count >= 6:
        score += CONFIDENCE_WEIGHT_COUNT_GE_6
        reason_codes.append("SUFFICIENT_TRANSACTION_HISTORY")
        explanation_parts.append(f"Observed {count} recurring transactions over 6+ months")
    elif count in (4, 5):
        score += CONFIDENCE_WEIGHT_COUNT_4_5
        reason_codes.append("SUFFICIENT_TRANSACTION_HISTORY")
        explanation_parts.append(f"Observed {count} transactions")
    elif count == 3:
        score += CONFIDENCE_WEIGHT_COUNT_3
        reason_codes.append("MODERATE_TRANSACTION_HISTORY")
        explanation_parts.append(f"Observed 3 transactions")
    elif count == 2:
        score += CONFIDENCE_WEIGHT_COUNT_2
        reason_codes.append("MINIMAL_TRANSACTION_HISTORY")
        explanation_parts.append(f"Observed 2 transactions")
    else:
        score += CONFIDENCE_WEIGHT_COUNT_1
        reason_codes.append("INSUFFICIENT_TRANSACTION_COUNT")
        explanation_parts.append(f"Only 1 transaction observed")

    # 2. Cadence & interval consistency
    cadence = cadence_res.cadence
    if cadence_res.is_candidate_only:
        reason_codes.append("SINGLE_ANNUAL_OBSERVATION_REQUIRES_MORE_EVIDENCE")
        explanation_parts.append("Single observation requires future billing cycle for confirmation")
    elif cadence in ("weekly", "fortnightly", "monthly", "variable_monthly", "quarterly", "annual"):
        if interval_info.std_dev_interval <= 2.0:
            score += CONFIDENCE_WEIGHT_INTERVAL_CONSISTENT
            reason_codes.append(f"REGULAR_{cadence.upper()}_CADENCE")
            explanation_parts.append(f"with highly regular {cadence.replace('_', ' ')} intervals (std dev {interval_info.std_dev_interval:.1f} days)")
        elif interval_info.std_dev_interval <= 5.0:
            score += CONFIDENCE_WEIGHT_INTERVAL_MODERATE
            reason_codes.append(f"REGULAR_{cadence.upper()}_CADENCE")
            explanation_parts.append(f"with regular {cadence.replace('_', ' ')} intervals")
        else:
            score += CONFIDENCE_WEIGHT_INTERVAL_IRREGULAR
            reason_codes.append("INTERVAL_VARIANCE_OBSERVED")
    elif cadence == "irregular":
        score += CONFIDENCE_WEIGHT_INTERVAL_IRREGULAR
        reason_codes.append("IRREGULAR_INTERVALS_DETECTED")
        explanation_parts.append("at irregular intervals (20-35 day frequency)")
    else:
        reason_codes.append("UNKNOWN_CADENCE")

    # 3. Amount pattern scoring
    if amount_info.amount_pattern == "fixed":
        score += CONFIDENCE_WEIGHT_AMOUNT_FIXED
        reason_codes.append("FIXED_AMOUNT_OBSERVED")
        explanation_parts.append(f"at a fixed amount of ₹{amount_info.representative_amount}")
    elif amount_info.amount_pattern == "variable":
        score += CONFIDENCE_WEIGHT_AMOUNT_VARIABLE
        reason_codes.append("VARIABLE_AMOUNT_OBSERVED")
        explanation_parts.append(f"with variable amounts between ₹{amount_info.amount_min} and ₹{amount_info.amount_max}")
    else:
        reason_codes.append("INSUFFICIENT_AMOUNT_HISTORY")

    # 4. Merchant resolution scoring
    if is_merchant_resolved:
        m_conf = (merchant_match_confidence or "medium").lower()
        if m_conf == "high":
            score += CONFIDENCE_WEIGHT_MERCHANT_HIGH
            reason_codes.append("HIGH_CONFIDENCE_MERCHANT_MATCH")
            explanation_parts.append(f"Merchant '{display_name}' verified with high confidence")
        else:
            score += CONFIDENCE_WEIGHT_MERCHANT_MEDIUM
            reason_codes.append("MODERATE_CONFIDENCE_MERCHANT_MATCH")
    else:
        score += CONFIDENCE_WEIGHT_MERCHANT_UNRESOLVED
        reason_codes.append("UNRESOLVED_MERCHANT_DESCRIPTOR")
        explanation_parts.append(f"Raw descriptor '{display_name}' unresolved to verified merchant")

    # 5. Payment channel recurring bonus
    channels = payment_channels or set()
    recurring_channel_names = {"upi_autopay", "mandate", "standing_instruction", "card_recurring"}
    if any(c in recurring_channel_names for c in channels):
        score += CONFIDENCE_WEIGHT_RECURRING_CHANNEL
        reason_codes.append("RECURRING_PAYMENT_CHANNEL_DETECTED")

    score = min(100.0, max(0.0, score))
    score_dec = Decimal(str(round(score, 2)))

    # Determine confidence band
    if not is_merchant_resolved:
        band = "needs_review"
    elif cadence_res.is_candidate_only:
        band = "low"
    elif score >= BAND_HIGH_THRESHOLD:
        band = "high"
    elif score >= BAND_MEDIUM_THRESHOLD:
        band = "medium"
    else:
        band = "low"

    full_explanation = ". ".join(explanation_parts) + "."
    return ConfidenceAssessment(
        score=score_dec,
        band=band,
        reason_codes=reason_codes,
        explanation=full_explanation,
    )
