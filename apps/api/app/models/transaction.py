"""Transaction SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Transaction(Base):
    """Observed financial transaction record parsed from a synthetic statement."""
    
    __tablename__ = "transactions"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "external_synthetic_id",
            name="uq_transactions_user_external_id",
        ),
        Index("ix_transactions_user_date", "user_id", "transaction_date"),
        Index("ix_transactions_user_norm_desc", "user_id", "normalised_descriptor"),
        Index("ix_transactions_user_merchant", "user_id", "merchant_id"),
        Index("ix_transactions_match_status", "user_id", "merchant_match_status"),
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
    account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    import_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("imports.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    external_synthetic_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    transaction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    posted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    raw_descriptor: Mapped[str] = mapped_column(Text, nullable=False)
    normalised_descriptor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    direction: Mapped[str] = mapped_column(String(10), default="debit", nullable=False)
    transaction_status: Mapped[str] = mapped_column(
        String(50),
        default="successful",
        nullable=False,
    )
    payment_channel: Mapped[str] = mapped_column(
        String(50),
        default="unknown",
        nullable=False,
    )
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source_row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    raw_source_snapshot: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Phase 4: Merchant Intelligence linking and match metadata
    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    merchant_match_status: Mapped[str] = mapped_column(
        String(50),
        default="unmatched",
        nullable=False,
    )  # unmatched, matched, needs_review, user_confirmed
    merchant_match_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # exact_canonical, exact_alias, regex_pattern, rapidfuzz, user_confirmed
    merchant_match_score: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )
    merchant_match_confidence: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )  # high, medium, low, none
    merchant_match_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    matched_descriptor_alias_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("descriptor_aliases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    matcher_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    matched_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="transactions")
    account: Mapped[Optional["Account"]] = relationship("Account", back_populates="transactions")
    import_record: Mapped[Optional["ImportRecord"]] = relationship("ImportRecord", back_populates="transactions")
    merchant: Mapped[Optional["Merchant"]] = relationship("Merchant", back_populates="transactions")
    matched_alias: Mapped[Optional["DescriptorAlias"]] = relationship("DescriptorAlias", back_populates="transactions")
    commitment_transactions: Mapped[List["CommitmentTransaction"]] = relationship(
        "CommitmentTransaction", back_populates="transaction", cascade="all, delete-orphan"
    )
