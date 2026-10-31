"""Cancellation Case SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import Any, List, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CancellationCase(Base):
    """User-guided recurring commitment cancellation case and checklist."""

    __tablename__ = "cancellation_cases"
    __table_args__ = (
        Index("ix_cancellation_cases_user_status", "user_id", "status"),
        Index("ix_cancellation_cases_commitment", "commitment_id"),
        Index("ix_cancellation_cases_created_at", "created_at"),
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
    cancellation_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cancellation_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    payment_mechanism: Mapped[str] = mapped_column(
        String(50),
        default="UNKNOWN",
        nullable=False,
    )  # UPI_AUTOPAY, E_NACH, CARD_SI, OTHER, UNKNOWN
    playbook_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="NOT_STARTED",
        nullable=False,
    )  # NOT_STARTED, GUIDANCE_REVIEWED, IN_PROGRESS, USER_REPORTED_CANCELLED, PENDING_VERIFICATION, VERIFIED_CANCELLED, UNABLE_TO_COMPLETE, CLOSED
    completed_steps: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    user_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    evidence_references: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    user_reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(
        Text,
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
    user: Mapped["DemoUser"] = relationship("DemoUser")
    commitment: Mapped["Commitment"] = relationship("Commitment")
    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant")
    cancellation_event: Mapped[Optional["CancellationEvent"]] = relationship("CancellationEvent")
