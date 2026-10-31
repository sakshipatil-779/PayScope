"""Commitment Insight SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CommitmentInsight(Base):
    """Actionable intelligence and anomaly insight linked to a recurring commitment."""

    __tablename__ = "commitment_insights"
    __table_args__ = (
        UniqueConstraint("unique_fingerprint", name="uq_commitment_insights_fingerprint"),
        Index("ix_commitment_insights_user_status", "user_id", "status"),
        Index("ix_commitment_insights_commitment_type", "commitment_id", "insight_type"),
        Index("ix_commitment_insights_detected_at", "detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("demo_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    insight_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # price_increase, trial_conversion, potentially_unused, post_cancellation_charge, unusual_amount, needs_review
    severity: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )  # info, low, medium, high, critical
    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
    )  # open, acknowledged, resolved, dismissed, needs_review
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    explanation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    confidence_band: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )  # high, medium, low, needs_review
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    detector_version: Mapped[str] = mapped_column(
        String(20),
        default="v1.0",
        nullable=False,
    )
    unique_fingerprint: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="insights")
    commitment: Mapped["Commitment"] = relationship("Commitment", back_populates="insights")
    evidence_items: Mapped[List["InsightEvidence"]] = relationship(
        "InsightEvidence",
        back_populates="insight",
        cascade="all, delete-orphan",
    )

