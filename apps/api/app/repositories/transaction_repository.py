"""Transaction repository operations."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.transaction import Transaction


class TransactionRepository:
    """Repository for Transaction persistence operations."""

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        raw_descriptor: str,
        amount: Decimal,
        transaction_date: datetime,
        account_id: Optional[uuid.UUID] = None,
        import_id: Optional[uuid.UUID] = None,
        external_synthetic_id: Optional[str] = None,
        currency: str = "INR",
        direction: str = "debit",
        transaction_status: str = "successful",
        payment_channel: str = "unknown",
        payment_reference: Optional[str] = None,
        normalised_descriptor: Optional[str] = None,
    ) -> Transaction:
        """Create and persist a new financial transaction record."""
        transaction = Transaction(
            user_id=user_id,
            account_id=account_id,
            import_id=import_id,
            external_synthetic_id=external_synthetic_id,
            transaction_date=transaction_date,
            raw_descriptor=raw_descriptor,
            normalised_descriptor=normalised_descriptor or raw_descriptor.strip(),
            amount=amount,
            currency=currency,
            direction=direction,
            transaction_status=transaction_status,
            payment_channel=payment_channel,
            payment_reference=payment_reference,
            is_synthetic=True,
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        return transaction

    @staticmethod
    def get_by_id(db: Session, transaction_id: uuid.UUID) -> Optional[Transaction]:
        """Retrieve a transaction by UUID."""
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        return db.scalar(stmt)

    @staticmethod
    def list_by_account(db: Session, account_id: uuid.UUID) -> List[Transaction]:
        """Retrieve all transactions associated with an account."""
        stmt = (
            select(Transaction)
            .where(Transaction.account_id == account_id)
            .order_by(Transaction.transaction_date.desc())
        )
        return list(db.scalars(stmt).all())
