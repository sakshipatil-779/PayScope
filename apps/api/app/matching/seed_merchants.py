"""Idempotent seed script to populate curated merchants and aliases into the database."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.matching.merchant_fixtures import CANONICAL_MERCHANT_REGISTRY
from app.matching.normalizer import DescriptorNormalizer
from app.models.descriptor_alias import DescriptorAlias
from app.models.merchant import Merchant


def seed_canonical_merchants(db: Session) -> dict[str, int]:
    """Seed canonical merchants and initial aliases idempotently."""
    created_merchants = 0
    created_aliases = 0
    existing_merchants = 0
    existing_aliases = 0

    for fixture in CANONICAL_MERCHANT_REGISTRY:
        # Check if merchant exists
        stmt = select(Merchant).where(Merchant.canonical_name == fixture.canonical_name)
        merchant = db.scalar(stmt)

        if not merchant:
            merchant = Merchant(
                canonical_name=fixture.canonical_name,
                category=fixture.category,
                commitment_type_default=fixture.commitment_type_default,
                website_url=fixture.website_url,
                support_url=fixture.support_url,
                is_fictional_demo_merchant=fixture.is_fictional,
                reference_source="seed_curated_demo_fixtures",
            )
            db.add(merchant)
            db.flush()
            created_merchants += 1
        else:
            existing_merchants += 1

        # Seed aliases for this merchant
        for alias_fix in fixture.aliases:
            norm_alias = DescriptorNormalizer.normalize(alias_fix.alias_text)
            if not norm_alias:
                continue

            # Check if alias already exists for this merchant
            alias_stmt = select(DescriptorAlias).where(
                DescriptorAlias.merchant_id == merchant.id,
                DescriptorAlias.normalised_alias == norm_alias,
            )
            existing_alias = db.scalar(alias_stmt)

            if not existing_alias:
                new_alias = DescriptorAlias(
                    merchant_id=merchant.id,
                    alias_text=alias_fix.alias_text,
                    normalised_alias=norm_alias,
                    matcher_type=alias_fix.matcher_type,
                    pattern=alias_fix.pattern,
                    confidence_band=alias_fix.confidence_band,
                    reference_source=alias_fix.reference_source,
                    is_active=True,
                )
                db.add(new_alias)
                created_aliases += 1
            else:
                existing_aliases += 1

    db.commit()
    return {
        "created_merchants": created_merchants,
        "existing_merchants": existing_merchants,
        "created_aliases": created_aliases,
        "existing_aliases": existing_aliases,
    }


def main():
    print("Starting canonical merchant and descriptor alias database seed...")
    with SessionLocal() as db:
        stats = seed_canonical_merchants(db)
        print(f"Seed complete:")
        print(f"  Merchants: {stats['created_merchants']} created, {stats['existing_merchants']} already existing")
        print(f"  Aliases:   {stats['created_aliases']} created, {stats['existing_aliases']} already existing")


if __name__ == "__main__":
    main()
