"""Cancellation Event SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CancellationEvent(Base):
    """Normalized cancellation event record for verifying post-cancellation charges."""

    __tablename__ = "cancellation_events"
    __table_args__ = (
        Index("ix_cancellation_events_user_commitment", "user_id", "commitment_id"),
        Index("ix_cancellation_events_timestamp", "event_timestamp"),
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
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_notification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payment_notifications.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    event_source: Mapped[str] = mapped_column(
        String(50),
        default="notification",
        nullable=False,
    )  # notification, user_recorded
    confirmation_type: Mapped[str] = mapped_column(
        String(50),
        default="explicit_notification",
        nullable=False,
    )  # explicit_notification, user_confirmed, inferred_needs_review
    evidence_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_synthetic: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="cancellation_events")
    commitment: Mapped["Commitment"] = relationship("Commitment", back_populates="cancellation_events")
    notification: Mapped[Optional["PaymentNotification"]] = relationship("PaymentNotification")

