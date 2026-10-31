"""Insight Evidence junction SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class InsightEvidence(Base):
    """Many-to-one evidence relation linking supporting records to an insight."""

    __tablename__ = "insight_evidence"
    __table_args__ = (
        Index("ix_insight_evidence_insight_id", "insight_id"),
        Index("ix_insight_evidence_transaction_id", "transaction_id"),
        Index("ix_insight_evidence_notification_id", "notification_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    insight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitment_insights.id", ondelete="CASCADE"),
        nullable=False,
    )
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=True,
    )
    notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_notifications.id", ondelete="CASCADE"),
        nullable=True,
    )
    usage_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usage_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    usage_coverage_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("usage_coverage.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancellation_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cancellation_events.id", ondelete="SET NULL"),
        nullable=True,
    )
    evidence_role: Mapped[str] = mapped_column(
        String(50),
        default="supporting_evidence",
        nullable=False,
    )  # previous_price_evidence, new_price_evidence, price_notification, trial_start_evidence, paid_conversion_evidence, usage_coverage_evidence, usage_event_evidence, cancellation_evidence, post_cancellation_debit, unusual_amount_evidence
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    insight: Mapped["CommitmentInsight"] = relationship(
        "CommitmentInsight",
        back_populates="evidence_items",
    )
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")
    notification: Mapped[Optional["PaymentNotification"]] = relationship("PaymentNotification")
    usage_event: Mapped[Optional["UsageEvent"]] = relationship("UsageEvent")
    usage_coverage: Mapped[Optional["UsageCoverage"]] = relationship("UsageCoverage")
    cancellation_event: Mapped[Optional["CancellationEvent"]] = relationship("CancellationEvent")
