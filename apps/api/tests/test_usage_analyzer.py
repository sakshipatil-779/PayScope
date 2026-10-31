"""Unit tests for usage analysis and inactivity intelligence."""
import uuid
from datetime import date, datetime, timezone
from app.analytics.insights.usage_analyzer import UsageAnalysisStatus, analyze_commitment_usage
from app.models.commitment import Commitment
from app.models.usage_coverage import UsageCoverage
from app.models.usage_event import UsageEvent


def test_potentially_unused_detected_with_complete_coverage():
    """Verify Zenith Fitness Club: complete 184-day coverage with 0 usage events."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="Zenith Fitness Club",
        commitment_type="membership",
        cadence="monthly",
    )

    cov = UsageCoverage(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        source_label="gym_rfid_turnstile",
        coverage_start=date(2026, 5, 1),
        coverage_end=date(2026, 10, 31),
        coverage_complete=True,
    )

    res = analyze_commitment_usage(commitment, coverage_records=[cov], usage_events=[])
    assert res.status == UsageAnalysisStatus.POTENTIALLY_UNUSED
    assert res.coverage_days >= 90
    assert res.usage_event_count == 0
    assert res.confidence_band == "high"
    assert "no recorded usage" in res.explanation.lower()


def test_incomplete_coverage_yields_insufficient_coverage():
    """Trust safeguard: Incomplete coverage cannot be marked as potentially unused."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="CloudStorage App",
        commitment_type="subscription",
        cadence="monthly",
    )

    cov = UsageCoverage(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        source_label="api_log",
        coverage_start=date(2026, 5, 1),
        coverage_end=date(2026, 10, 31),
        coverage_complete=False,
        coverage_notes="Data sync gap between July and August",
    )

    res = analyze_commitment_usage(commitment, coverage_records=[cov], usage_events=[])
    assert res.status == UsageAnalysisStatus.INSUFFICIENT_COVERAGE
    assert "incomplete" in res.explanation.lower()


def test_missing_coverage_yields_usage_unavailable():
    """Absence of evidence is not evidence of absence: missing coverage returns USAGE_UNAVAILABLE."""
    commitment = Commitment(
        id=uuid.uuid4(),
        display_name="StreamPulse Entertainment",
        commitment_type="subscription",
        cadence="monthly",
    )

    res = analyze_commitment_usage(commitment, coverage_records=[], usage_events=[])
    assert res.status == UsageAnalysisStatus.USAGE_UNAVAILABLE
    assert res.confidence_band == "none"


def test_active_usage_events_yield_usage_observed():
    """When usage events exist, status is USAGE_OBSERVED."""
    uid = uuid.uuid4()
    commitment = Commitment(
        id=uuid.uuid4(),
        user_id=uid,
        display_name="Zenith Fitness Club",
        commitment_type="membership",
        cadence="monthly",
    )

    cov = UsageCoverage(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        source_label="gym_rfid_turnstile",
        coverage_start=date(2026, 5, 1),
        coverage_end=date(2026, 10, 31),
        coverage_complete=True,
    )

    event = UsageEvent(
        id=uuid.uuid4(),
        user_id=uid,
        commitment_id=commitment.id,
        event_at=datetime(2026, 6, 15, 18, 30, tzinfo=timezone.utc),
        event_type="gym_checkin",
        source_label="gym_rfid_turnstile",
    )

    res = analyze_commitment_usage(commitment, coverage_records=[cov], usage_events=[event])
    assert res.status == UsageAnalysisStatus.USAGE_OBSERVED
    assert res.usage_event_count == 1
