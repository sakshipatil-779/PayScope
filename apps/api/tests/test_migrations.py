"""Integration tests verifying Alembic migration upgrade and downgrade cycles."""
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from app.core.config import settings


def get_test_alembic_config() -> Config:
    """Create an Alembic config targeted at the test database."""
    cfg = Config("alembic.ini")
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
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('demo_users', 'transactions', 'accounts');"
            )
        ).scalar()
        assert result == 0

    # Step 2: Re-upgrade to head
    command.upgrade(cfg, "head")

    # Verify tables are recreated
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('demo_users', 'transactions', 'accounts');"
            )
        ).scalar()
        assert result == 3
