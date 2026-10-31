"""Audit Event SQLAlchemy 2.0 model."""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class AuditEvent(Base):
    """Audit event for recording user actions and algorithmic state transitions."""
    
    __tablename__ = "audit_events"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("demo_users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    before_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    after_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    actor_type: Mapped[str] = mapped_column(String(50), default="system", nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    
    # Relationships
    user: Mapped[Optional["DemoUser"]] = relationship("DemoUser", back_populates="audit_events")
