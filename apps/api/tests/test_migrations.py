"""Integration tests verifying Alembic migration upgrade and downgrade cycles."""
from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from app.core.config import settings

CHECKED_TABLES = (
    "'demo_users', 'transactions', 'accounts', 'commitments', 'commitment_transactions', "
    "'price_events', 'commitment_insights', 'insight_evidence', 'usage_events', 'usage_coverage', 'cancellation_events'"
)


def get_test_alembic_config() -> Config:
    """Create an Alembic config targeted at the test database."""
    ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    return cfg


def test_migration_downgrade_and_reupgrade(engine):
    """Verify that Alembic can downgrade to base and re-upgrade to head cleanly."""
    cfg = get_test_alembic_config()

    # Step 1: Downgrade to base
    command.downgrade(cfg, "base")

    # Verify tables are dropped
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ({CHECKED_TABLES});"
            )
        ).scalar()
        assert result == 0

    # Step 2: Re-upgrade to head
    command.upgrade(cfg, "head")

    # Verify tables are recreated
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ({CHECKED_TABLES});"
            )
        ).scalar()
        assert result == 11
