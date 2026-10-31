"""Payment Notification SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PaymentNotification(Base):
    """Synthetic payment or mandate notification record for multi-modal evidence."""

    __tablename__ = "payment_notifications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "external_synthetic_id",
            name="uq_notifications_user_external_id",
        ),
        Index("ix_notifications_user_timestamp", "user_id", "event_timestamp"),
        Index("ix_notifications_user_event_type", "user_id", "event_type"),
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
    import_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("imports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_synthetic_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    event_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    merchant_hint: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    currency: Mapped[Optional[str]] = mapped_column(
        String(3),
        default="INR",
        nullable=True,
    )
    payment_mechanism: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    mandate_external_ref: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    message_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    raw_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
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
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="payment_notifications")
    import_record: Mapped[Optional["ImportRecord"]] = relationship(
        "ImportRecord",
        back_populates="payment_notifications",
    )

