"""Manual Review Item SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from sqlalchemy import (
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


class ManualReviewItem(Base):
    """Queued item for manual human review of ambiguous or low-confidence matches."""

    __tablename__ = "manual_review_items"
    __table_args__ = (
        Index("ix_manual_review_items_user_status", "user_id", "status"),
        Index("ix_manual_review_items_raw_desc", "user_id", "raw_descriptor"),
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
    transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="merchant_match",
    )  # merchant_match, recurring_cluster, price_event, usage_signal, other
    raw_descriptor: Mapped[str] = mapped_column(Text, nullable=False)
    normalised_descriptor: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    candidate_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    similarity_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    confidence_band: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    match_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="ambiguous_match",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open",
    )  # open, accepted, corrected, dismissed
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    decision_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_selected_merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
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
    transaction: Mapped[Optional["Transaction"]] = relationship("Transaction")
    suggested_merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        foreign_keys=[suggested_merchant_id],
    )
    user_selected_merchant: Mapped[Optional["Merchant"]] = relationship(
        "Merchant",
        foreign_keys=[user_selected_merchant_id],
    )
