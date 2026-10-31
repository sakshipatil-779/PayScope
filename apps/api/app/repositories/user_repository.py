"""Demo User repository operations."""
import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.demo_user import DemoUser


class UserRepository:
    """Repository for DemoUser persistence operations."""

    @staticmethod
    def create(
        db: Session,
        workspace_key: str,
        display_name: Optional[str] = "Demo User",
        home_currency: str = "INR",
        is_demo: bool = True,
    ) -> DemoUser:
        """Create and persist a new demo user."""
        user = DemoUser(
            workspace_key=workspace_key,
            display_name=display_name,
            home_currency=home_currency,
            is_demo=is_demo,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> Optional[DemoUser]:
        """Retrieve a demo user by UUID."""
        stmt = select(DemoUser).where(DemoUser.id == user_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_workspace_key(db: Session, workspace_key: str) -> Optional[DemoUser]:
        """Retrieve a demo user by unique workspace key."""
        stmt = select(DemoUser).where(DemoUser.workspace_key == workspace_key)
        return db.scalar(stmt)

    @classmethod
    def get_or_create_demo_user(
        cls,
        db: Session,
        workspace_key: str = "demo_workspace_primary",
        display_name: str = "Demo User",
    ) -> DemoUser:
        """Retrieve existing demo user or create one if not found."""
        user = cls.get_by_workspace_key(db, workspace_key)
        if not user:
            user = cls.create(db, workspace_key=workspace_key, display_name=display_name)
        return user
