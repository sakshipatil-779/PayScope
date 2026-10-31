"""Descriptor Alias SQLAlchemy 2.0 model."""
import uuid
from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DescriptorAlias(Base):
    """Hand-curated and user-confirmed descriptor alias for a canonical merchant."""

    __tablename__ = "descriptor_aliases"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "normalised_alias",
            name="uq_descriptor_aliases_merchant_normalised_alias",
        ),
        Index("ix_descriptor_aliases_norm_active", "normalised_alias", "is_active"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("merchants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias_text: Mapped[str] = mapped_column(String(255), nullable=False)
    normalised_alias: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    matcher_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="exact",
    )  # exact, prefix, regex, token_pattern
    pattern: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence_band: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="high",
    )  # high, medium, low
    reference_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    merchant: Mapped["Merchant"] = relationship("Merchant", back_populates="aliases")
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="matched_alias",
    )
