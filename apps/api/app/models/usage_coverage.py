"""Usage Coverage SQLAlchemy 2.0 model."""
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Date,
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


class UsageCoverage(Base):
    """Observation period record for which service usage logs are known to exist or be absent."""

    __tablename__ = "usage_coverage"
    __table_args__ = (
        Index("ix_usage_coverage_user_commitment", "user_id", "commitment_id"),
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
    source_label: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    coverage_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    coverage_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    coverage_complete: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    coverage_notes: Mapped[Optional[str]] = mapped_column(
        Text,
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
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="usage_coverage")
    commitment: Mapped["Commitment"] = relationship("Commitment", back_populates="usage_coverage")

