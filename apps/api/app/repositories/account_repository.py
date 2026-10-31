"""Account repository operations."""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.account import Account


class AccountRepository:
    """Repository for Account persistence operations."""

    @staticmethod
    def create(
        db: Session,
        user_id: uuid.UUID,
        label: str,
        account_type: str = "bank_statement",
        institution_label: Optional[str] = None,
        masked_reference: Optional[str] = None,
        currency: str = "INR",
        is_synthetic: bool = True,
    ) -> Account:
        """Create and persist a new synthetic account."""
        account = Account(
            user_id=user_id,
            label=label,
            account_type=account_type,
            institution_label=institution_label,
            masked_reference=masked_reference,
            currency=currency,
            is_synthetic=is_synthetic,
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def get_by_id(db: Session, account_id: uuid.UUID) -> Optional[Account]:
        """Retrieve an account by UUID."""
        stmt = select(Account).where(Account.id == account_id)
        return db.scalar(stmt)

    @staticmethod
    def list_by_user(db: Session, user_id: uuid.UUID) -> List[Account]:
        """List all accounts belonging to a user."""
        stmt = select(Account).where(Account.user_id == user_id)
        return list(db.scalars(stmt).all())
