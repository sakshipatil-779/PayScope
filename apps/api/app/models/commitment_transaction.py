"""Commitment Transaction junction SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class CommitmentTransaction(Base):
    """Many-to-many evidence relation between commitments and transactions."""

    __tablename__ = "commitment_transactions"
    __table_args__ = (
        UniqueConstraint(
            "commitment_id",
            "transaction_id",
            name="uq_commitment_transactions_commitment_transaction",
        ),
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
        index=True,
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_role: Mapped[str] = mapped_column(
        String(50),
        default="recurrence_evidence",
        nullable=False,
    )  # recurrence_evidence, amount_change_evidence, post_cancellation_charge, excluded_candidate
    match_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    reason: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    commitment: Mapped["Commitment"] = relationship(
        "Commitment",
        back_populates="commitment_transactions",
    )
    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="commitment_transactions",
    )
