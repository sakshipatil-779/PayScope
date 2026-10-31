"""Usage Event SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class UsageEvent(Base):
    """Synthetic service or facility usage event (e.g. gym check-in, streaming session)."""

    __tablename__ = "usage_events"
    __table_args__ = (
        Index("ix_usage_events_user_commitment", "user_id", "commitment_id"),
        Index("ix_usage_events_event_at", "event_at"),
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
    commitment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("commitments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # app_open, streaming_session, gym_checkin, cloud_activity, user_confirmed_use, other
    event_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    source_label: Mapped[str] = mapped_column(
        String(100),
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
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="usage_events")
    commitment: Mapped[Optional["Commitment"]] = relationship("Commitment", back_populates="usage_events")

