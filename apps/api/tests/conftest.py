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

# Test database engine connected to mandatelens_test
test_engine = create_engine(
    settings.TEST_DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
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
                    "TRUNCATE TABLE transactions, imports, accounts, audit_events, merchants, demo_users CASCADE;"
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
