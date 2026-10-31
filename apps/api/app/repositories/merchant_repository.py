"""Merchant repository operations."""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.merchant import Merchant


class MerchantRepository:
    """Repository for Merchant reference operations."""

    @staticmethod
    def create(
        db: Session,
        canonical_name: str,
        category: str,
        commitment_type_default: Optional[str] = None,
        website_url: Optional[str] = None,
        support_url: Optional[str] = None,
        is_fictional_demo_merchant: bool = True,
        reference_source: Optional[str] = "internal_curated",
    ) -> Merchant:
        """Create and persist a canonical merchant reference record."""
        merchant = Merchant(
            canonical_name=canonical_name,
            category=category,
            commitment_type_default=commitment_type_default,
            website_url=website_url,
            support_url=support_url,
            is_fictional_demo_merchant=is_fictional_demo_merchant,
            reference_source=reference_source,
        )
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return merchant

    @staticmethod
    def get_by_id(db: Session, merchant_id: uuid.UUID) -> Optional[Merchant]:
        """Retrieve a merchant by UUID."""
        stmt = select(Merchant).where(Merchant.id == merchant_id)
        return db.scalar(stmt)

    @staticmethod
    def get_by_canonical_name(db: Session, canonical_name: str) -> Optional[Merchant]:
        """Retrieve a merchant by unique canonical name."""
        stmt = select(Merchant).where(Merchant.canonical_name == canonical_name)
        return db.scalar(stmt)

    @staticmethod
    def list_all(db: Session) -> List[Merchant]:
        """List all canonical merchants."""
        stmt = select(Merchant).order_by(Merchant.canonical_name.asc())
        return list(db.scalars(stmt).all())
