"""Merchant SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import Boolean, Date, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Merchant(Base):
    """Canonical merchant reference record for descriptor resolution."""
    
    __tablename__ = "merchants"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    canonical_name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    commitment_type_default: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    support_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_fictional_demo_merchant: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reference_source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    verified_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
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
