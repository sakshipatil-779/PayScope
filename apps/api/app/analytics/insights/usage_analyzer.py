"""Service usage intelligence and inactivity analysis engine."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import List, Optional
from app.analytics.insights.config import DETECTOR_VERSION, UsageAnalysisThresholds
from app.models.commitment import Commitment
from app.models.usage_coverage import UsageCoverage
from app.models.usage_event import UsageEvent

thresholds = UsageAnalysisThresholds()


@dataclass
class UsageAnalysisResult:
    """Detailed outcome of usage coverage and activity evaluation."""
    commitment_id: str
    status: str  # POTENTIALLY_UNUSED, USAGE_OBSERVED, USAGE_UNAVAILABLE, INSUFFICIENT_COVERAGE
    coverage_days: int = 0
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    usage_event_count: int = 0
    confidence_score: Optional[Decimal] = None
    confidence_band: str = "none"
    explanation: str = ""
    detector_version: str = DETECTOR_VERSION
    coverage_record: Optional[UsageCoverage] = None
    observed_events: List[UsageEvent] = None


def analyze_commitment_usage(
    commitment: Commitment,
    coverage_records: List[UsageCoverage],
    usage_events: List[UsageEvent],
) -> UsageAnalysisResult:
    """Analyze service usage and explicit observation coverage for a commitment.
    
    CRITICAL TRUST PRINCIPLE:
    Absence of evidence is NOT evidence of absence. A service is labeled as
    POTENTIALLY_UNUSED only when an explicit, complete observation coverage
    record spans at least 90 days and zero usage events occurred in that window.
    
    States:
    - POTENTIALLY_UNUSED: Complete coverage >= 90 days with 0 recorded events.
    - USAGE_OBSERVED: At least 1 linked usage event exists.
    - USAGE_UNAVAILABLE: No coverage record exists.
    - INSUFFICIENT_COVERAGE: Coverage record exists but is incomplete or < 90 days.
    
    Args:
        commitment: The Commitment model instance.
        coverage_records: List of usage coverage logs for this commitment.
        usage_events: List of observed usage events for this commitment.
        
    Returns:
        UsageAnalysisResult with explicit status classification and evidence.
    """
    comm_id = str(commitment.id)

    # 1. Check for coverage records
    if not coverage_records:
        return UsageAnalysisResult(
            commitment_id=comm_id,
            status="USAGE_UNAVAILABLE",
            explanation=f"No usage tracking or login coverage record is available for {commitment.display_name}.",
            confidence_band="none",
        )

    # Take the latest/longest coverage record
    coverage = max(
        coverage_records,
        key=lambda c: ((c.coverage_end - c.coverage_start).days, c.created_at),
    )
    duration_days = (coverage.coverage_end - coverage.coverage_start).days

    # Filter usage events that fall within the coverage window
    events_in_window = [
        ev for ev in usage_events
        if coverage.coverage_start <= ev.event_at.date() <= coverage.coverage_end
    ]

    # 2. Check if usage was observed
    if len(events_in_window) > 0:
        return UsageAnalysisResult(
            commitment_id=comm_id,
            status="USAGE_OBSERVED",
            coverage_days=duration_days,
            coverage_start=coverage.coverage_start,
            coverage_end=coverage.coverage_end,
            usage_event_count=len(events_in_window),
            confidence_score=Decimal("95.00"),
            confidence_band="high",
            explanation=f"Observed {len(events_in_window)} activity events for {commitment.display_name} within the {duration_days}-day coverage window.",
            coverage_record=coverage,
            observed_events=events_in_window,
        )

    # 3. Check coverage completeness and minimum observation duration
    if not coverage.coverage_complete or duration_days < thresholds.min_observation_window_days:
        reason = "incomplete coverage log" if not coverage.coverage_complete else f"coverage period ({duration_days} days) is shorter than 90 days"
        return UsageAnalysisResult(
            commitment_id=comm_id,
            status="INSUFFICIENT_COVERAGE",
            coverage_days=duration_days,
            coverage_start=coverage.coverage_start,
            coverage_end=coverage.coverage_end,
            usage_event_count=0,
            confidence_band="low",
            explanation=f"Insufficient evidence to assess usage for {commitment.display_name}: {reason}.",
            coverage_record=coverage,
            observed_events=[],
        )

    # 4. POTENTIALLY UNUSED: Complete coverage >= 90 days with 0 events
    explanation = (
        f"This membership has no recorded usage during the last {duration_days} days of "
        f"covered activity (tracked via {coverage.source_label}). "
        f"Monthly recurring spend: ₹{commitment.representative_amount}."
    )

    return UsageAnalysisResult(
        commitment_id=comm_id,
        status="POTENTIALLY_UNUSED",
        coverage_days=duration_days,
        coverage_start=coverage.coverage_start,
        coverage_end=coverage.coverage_end,
        usage_event_count=0,
        confidence_score=Decimal("90.00"),
        confidence_band="high",
        explanation=explanation,
        coverage_record=coverage,
        observed_events=[],
    )


class UsageAnalysisStatus:
    POTENTIALLY_UNUSED = "POTENTIALLY_UNUSED"
    USAGE_OBSERVED = "USAGE_OBSERVED"
    USAGE_UNAVAILABLE = "USAGE_UNAVAILABLE"
    INSUFFICIENT_COVERAGE = "INSUFFICIENT_COVERAGE"


def analyze_usage(
    commitment: Commitment,
    transactions: list = None,
    coverage_records: List[UsageCoverage] = None,
    usage_events: List[UsageEvent] = None,
) -> UsageAnalysisResult:
    """Wrapper supporting transactions parameter."""
    return analyze_commitment_usage(
        commitment,
        coverage_records or [],
        usage_events or [],
    )
