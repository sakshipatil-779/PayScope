"""Pytest configuration and test database fixtures."""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.session import get_db
from app.main import app

# Explicit safety check: test engine must point strictly to test database
assert "mandatelens_test" in settings.TEST_DATABASE_URL, (
    f"FATAL: Safety check failed! TEST_DATABASE_URL points to non-test database: {settings.TEST_DATABASE_URL}"
)

# Test database engine connected to mandatelens_test
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

assert "mandatelens_test" in str(test_engine.url), (
    f"FATAL: Safety check failed! test_engine URL is not mandatelens_test: {test_engine.url}"
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def engine():
    """Session-scoped database engine fixture."""
    yield test_engine


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Function-scoped clean database session fixture.
    
    Truncates test tables after each test to ensure test isolation.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        # Clean up data between tests
        with test_engine.begin() as conn:
            conn.execute(
                text(
                    "TRUNCATE TABLE commitment_transactions, commitments, manual_review_items, descriptor_aliases, payment_notifications, transactions, imports, accounts, audit_events, merchants, demo_users CASCADE;"
                )
            )
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient fixture overriding get_db with the test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
