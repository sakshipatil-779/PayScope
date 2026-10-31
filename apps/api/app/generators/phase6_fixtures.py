"""Seed fixtures for Phase 6 anomaly intelligence (usage coverage and cancellation events)."""
import uuid
from datetime import date, datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.usage_coverage import UsageCoverage


def seed_phase6_supporting_data(db: Session, user_id: uuid.UUID) -> None:
    """Idempotently seed usage coverage records and cancellation events for the demo user."""
    # 1. Look up Zenith Fitness Club commitment
    zenith_stmt = (
        select(Commitment)
        .where(
            Commitment.user_id == user_id,
            Commitment.display_name.ilike("%Zenith Fitness%"),
        )
    )
    zenith = db.execute(zenith_stmt).scalars().first()

    if zenith:
        cov_stmt = select(UsageCoverage).where(UsageCoverage.commitment_id == zenith.id)
        existing_cov = db.execute(cov_stmt).scalars().first()
        if not existing_cov:
            cov = UsageCoverage(
                id=uuid.uuid4(),
                user_id=user_id,
                commitment_id=zenith.id,
                source_label="gym_rfid_turnstile",
                coverage_start=date(2026, 5, 1),
                coverage_end=date(2026, 10, 31),
                coverage_complete=True,
                coverage_notes=None,
                is_synthetic=True,
            )
            db.add(cov)

    # 2. Look up SkyVault Backup commitment
    skyvault_stmt = (
        select(Commitment)
        .where(
            Commitment.user_id == user_id,
            Commitment.display_name.ilike("%SkyVault%"),
        )
    )
    skyvault = db.execute(skyvault_stmt).scalars().first()

    if skyvault:
        cancel_stmt = select(CancellationEvent).where(CancellationEvent.commitment_id == skyvault.id)
        existing_cancel = db.execute(cancel_stmt).scalars().first()
        if not existing_cancel:
            cancel_evt = CancellationEvent(
                id=uuid.uuid4(),
                user_id=user_id,
                commitment_id=skyvault.id,
                merchant_id=skyvault.merchant_id,
                event_timestamp=datetime(2026, 7, 20, 14, 30, tzinfo=timezone.utc),
                event_source="notification",
                confirmation_type="explicit_notification",
                evidence_description="Subscription cancellation confirmation processed on 20-Jul-2026.",
                is_synthetic=True,
            )
            db.add(cancel_evt)

    db.commit()
