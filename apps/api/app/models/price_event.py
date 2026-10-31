"""Price Event SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PriceEvent(Base):
    """Structured monetary change event inside a recurring commitment."""

    __tablename__ = "price_events"
    __table_args__ = (
        Index("ix_price_events_commitment_id", "commitment_id"),
        Index("ix_price_events_detected_at", "effective_or_detected_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    commitment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitments.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # amount_increase, amount_decrease, trial_to_paid, promotional_period_end, needs_review
    previous_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    new_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )
    absolute_change: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    percentage_change: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(9, 4),
        nullable=True,
    )
    effective_or_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    confidence_band: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
    )  # high, medium, low, needs_review
    explanation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    detector_version: Mapped[str] = mapped_column(
        String(20),
        default="v1.0",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    commitment: Mapped["Commitment"] = relationship("Commitment", back_populates="price_events")

