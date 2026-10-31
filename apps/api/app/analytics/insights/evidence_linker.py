"""Evidence linking helpers for connecting insights to source financial records."""
import uuid
from typing import List, Optional
from app.models.cancellation_event import CancellationEvent
from app.models.insight_evidence import InsightEvidence
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction
from app.models.usage_coverage import UsageCoverage
from app.models.usage_event import UsageEvent


def create_transaction_evidence(
    insight_id: uuid.UUID,
    transaction: Transaction,
    role: str,
) -> InsightEvidence:
    """Create an evidence record linking a transaction to an insight."""
    return InsightEvidence(
        id=uuid.uuid4(),
        insight_id=insight_id,
        transaction_id=transaction.id,
        evidence_role=role,
    )


def create_notification_evidence(
    insight_id: uuid.UUID,
    notification: PaymentNotification,
    role: str,
) -> InsightEvidence:
    """Create an evidence record linking a payment notification to an insight."""
    return InsightEvidence(
        id=uuid.uuid4(),
        insight_id=insight_id,
        notification_id=notification.id,
        evidence_role=role,
    )


def create_coverage_evidence(
    insight_id: uuid.UUID,
    coverage: UsageCoverage,
    role: str = "usage_coverage_evidence",
) -> InsightEvidence:
    """Create an evidence record linking a usage coverage record to an insight."""
    return InsightEvidence(
        id=uuid.uuid4(),
        insight_id=insight_id,
        usage_coverage_id=coverage.id,
        evidence_role=role,
    )


def create_cancellation_evidence(
    insight_id: uuid.UUID,
    cancellation_event: CancellationEvent,
    role: str = "cancellation_evidence",
) -> InsightEvidence:
    """Create an evidence record linking a cancellation event to an insight."""
    return InsightEvidence(
        id=uuid.uuid4(),
        insight_id=insight_id,
        cancellation_event_id=cancellation_event.id,
        evidence_role=role,
    )

