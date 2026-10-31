"""Payment Notification repository operations."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.payment_notification import PaymentNotification


class PaymentNotificationRepository:
    """Repository for PaymentNotification persistence operations."""

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        external_synthetic_id: str,
        event_timestamp: datetime,
        event_type: str,
        message_text: str,
        import_id: Optional[uuid.UUID] = None,
        merchant_hint: Optional[str] = None,
        amount: Optional[Decimal] = None,
        currency: Optional[str] = "INR",
        payment_mechanism: Optional[str] = None,
        mandate_external_ref: Optional[str] = None,
        raw_payload: Optional[Dict[str, Any]] = None,
    ) -> PaymentNotification:
        """Create and persist a new payment notification record."""
        notification = PaymentNotification(
            user_id=user_id,
            import_id=import_id,
            external_synthetic_id=external_synthetic_id,
            event_timestamp=event_timestamp,
            event_type=event_type,
            merchant_hint=merchant_hint,
            amount=amount,
            currency=currency,
            payment_mechanism=payment_mechanism,
            mandate_external_ref=mandate_external_ref,
            message_text=message_text,
            raw_payload=raw_payload,
            is_synthetic=True,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_by_id(db: Session, notification_id: uuid.UUID) -> Optional[PaymentNotification]:
        """Retrieve a notification by UUID."""
        stmt = select(PaymentNotification).where(PaymentNotification.id == notification_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_external_id(
        db: Session, user_id: uuid.UUID, external_synthetic_id: str
    ) -> Optional[PaymentNotification]:
        """Retrieve a notification by user and external synthetic ID."""
        stmt = select(PaymentNotification).where(
            PaymentNotification.user_id == user_id,
            PaymentNotification.external_synthetic_id == external_synthetic_id,
        )
        return db.scalar(stmt)

    @staticmethod
    def list_by_user(
        db: Session, user_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> List[PaymentNotification]:
        """Retrieve notifications for a user ordered by timestamp."""
        stmt = (
            select(PaymentNotification)
            .where(PaymentNotification.user_id == user_id)
            .order_by(PaymentNotification.event_timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(db.scalars(stmt).all())
