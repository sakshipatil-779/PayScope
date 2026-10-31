"""Demo User SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class DemoUser(Base):
    """Demo workspace user record representing synthetic workspace owner."""
    
    __tablename__ = "demo_users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    workspace_key: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    home_currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
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
    accounts: Mapped[List["Account"]] = relationship(
        "Account",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    imports: Mapped[List["ImportRecord"]] = relationship(
        "ImportRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    payment_notifications: Mapped[List["PaymentNotification"]] = relationship(
        "PaymentNotification",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_events: Mapped[List["AuditEvent"]] = relationship(
        "AuditEvent",
        back_populates="user",
    )
    commitments: Mapped[List["Commitment"]] = relationship(
        "Commitment",
        back_populates="user",
        cascade="all, delete-orphan",
    )
