"""SavingsScenario SQLAlchemy 2.0 model for Phase 7 What-If projections."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
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


class SavingsScenario(Base):
    """User-created or simulated what-if savings scenario."""

    __tablename__ = "savings_scenarios"
    __table_args__ = (
        Index("ix_savings_scenarios_user_id", "user_id"),
        Index("ix_savings_scenarios_created_at", "created_at"),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_opportunity_ids: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    selected_commitment_ids: Mapped[List[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    baseline_annual_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    projected_annual_cost: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    annual_savings: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    monthly_savings: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    percentage_reduction: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        default=dict,
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
    user: Mapped["DemoUser"] = relationship("DemoUser", back_populates="savings_scenarios")

