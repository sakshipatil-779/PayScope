"""Commitment SQLAlchemy 2.0 model."""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Commitment(Base):
    """Inferred or user-confirmed recurring financial obligation."""

    __tablename__ = "commitments"
    __table_args__ = (
        Index("ix_commitments_user_id_status", "user_id", "status"),
        Index("ix_commitments_user_id_cadence", "user_id", "cadence"),
        Index("ix_commitments_user_id_merchant", "user_id", "merchant_id"),
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
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    commitment_type: Mapped[str] = mapped_column(
        String(50),
        default="subscription",
        nullable=False,
    )  # subscription, membership, utility, insurance, loan_emi, other, needs_review
    cadence: Mapped[str] = mapped_column(
        String(50),
        default="monthly",
        nullable=False,
    )  # weekly, fortnightly, monthly, quarterly, annual, variable_monthly, irregular, unknown
    amount_pattern: Mapped[str] = mapped_column(
        String(50),
        default="fixed",
        nullable=False,
    )  # fixed, variable, insufficient_data
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
    )  # candidate, active, user_confirmed, review_required, marked_not_recurring, ended_user_recorded, inactive
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    representative_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    amount_min: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    amount_max: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    next_expected_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )
    annualised_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    annualisation_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
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
    detection_reason_codes: Mapped[Optional[List[str]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    detection_explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    detector_version: Mapped[str] = mapped_column(
        String(20),
        default="v1.0",
        nullable=False,
    )
    user_decision: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # confirmed, corrected, not_recurring
    user_decision_at: Mapped[Optional[datetime]] = mapped_column(
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
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="commitments")
    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant", back_populates="commitments")
    commitment_transactions: Mapped[List["CommitmentTransaction"]] = relationship(
        "CommitmentTransaction",
        back_populates="commitment",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        secondary="commitment_transactions",
        viewonly=True,
        order_by="Transaction.transaction_date.desc()",
    )
    price_events: Mapped[List["PriceEvent"]] = relationship(
        "PriceEvent",
        back_populates="commitment",
        cascade="all, delete-orphan",
    )
    insights: Mapped[List["CommitmentInsight"]] = relationship(
        "CommitmentInsight",
        back_populates="commitment",
        cascade="all, delete-orphan",
    )
    usage_events: Mapped[List["UsageEvent"]] = relationship(
        "UsageEvent",
        back_populates="commitment",
    )
    usage_coverage: Mapped[List["UsageCoverage"]] = relationship(
        "UsageCoverage",
        back_populates="commitment",
        cascade="all, delete-orphan",
    )
    cancellation_events: Mapped[List["CancellationEvent"]] = relationship(
        "CancellationEvent",
        back_populates="commitment",
        cascade="all, delete-orphan",
    )
