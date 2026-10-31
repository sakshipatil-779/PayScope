"""Integration tests for PostgreSQL persistence and constraints."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.models.account import Account
from app.models.demo_user import DemoUser
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.repositories.account_repository import AccountRepository
from app.repositories.import_repository import ImportRepository
from app.repositories.merchant_repository import MerchantRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository


def test_database_connection(db_session: Session):
    """Verify raw connectivity to the test PostgreSQL database."""
    result = db_session.execute(text("SELECT 1 AS alive")).scalar()
    assert result == 1


def test_demo_user_insertion_and_retrieval(db_session: Session):
    """Verify demo user can be inserted and retrieved by UUID and workspace_key."""
    workspace_key = f"ws_test_{uuid.uuid4().hex[:8]}"
    created = UserRepository.create(
        db_session,
        workspace_key=workspace_key,
        display_name="Test FinTech User",
        home_currency="INR",
    )
    assert created.id is not None
    assert created.workspace_key == workspace_key
    assert created.home_currency == "INR"
    assert created.is_demo is True

    # Retrieve by ID
    retrieved_by_id = UserRepository.get_by_id(db_session, created.id)
    assert retrieved_by_id is not None
    assert retrieved_by_id.id == created.id
    assert retrieved_by_id.workspace_key == workspace_key

    # Retrieve by workspace_key
    retrieved_by_key = UserRepository.get_by_workspace_key(db_session, workspace_key)
    assert retrieved_by_key is not None
    assert retrieved_by_key.id == created.id


def test_account_insertion_and_user_relationship(db_session: Session):
    """Verify synthetic account insertion associated with a valid user."""
    user = UserRepository.create(
        db_session,
        workspace_key=f"ws_acc_{uuid.uuid4().hex[:8]}",
        display_name="Account Test User",
    )

    account = AccountRepository.create(
        db_session,
        user_id=user.id,
        label="HDFC Salary Synthetic",
        account_type="bank_statement",
        institution_label="HDFC Bank",
        masked_reference="**4321",
        currency="INR",
    )

    assert account.id is not None
    assert account.user_id == user.id
    assert account.label == "HDFC Salary Synthetic"
    assert account.is_synthetic is True

    # List by user
    accounts = AccountRepository.list_by_user(db_session, user.id)
    assert len(accounts) == 1
    assert accounts[0].id == account.id


def test_transaction_persistence(db_session: Session):
    """Verify synthetic transaction persistence with precise Numeric amount."""
    user = UserRepository.create(
        db_session,
        workspace_key=f"ws_tx_{uuid.uuid4().hex[:8]}",
    )
    account = AccountRepository.create(
        db_session,
        user_id=user.id,
        label="Main Account",
    )
    import_rec = ImportRepository.create(
        db_session,
        user_id=user.id,
        account_id=account.id,
        filename_display="test_statement.csv",
        storage_key=f"storage_{uuid.uuid4().hex}",
    )

    now_utc = datetime.now(timezone.utc)
    amount = Decimal("649.00")

    tx = TransactionRepository.create(
        db_session,
        user_id=user.id,
        account_id=account.id,
        import_id=import_rec.id,
        external_synthetic_id="SYN_TX_001",
        transaction_date=now_utc,
        raw_descriptor="NETFLIX MUMBAI IN",
        normalised_descriptor="NETFLIX",
        amount=amount,
        currency="INR",
        direction="debit",
        payment_channel="card",
    )

    assert tx.id is not None
    assert tx.amount == Decimal("649.00")
    assert tx.currency == "INR"
    assert tx.raw_descriptor == "NETFLIX MUMBAI IN"
    assert tx.normalised_descriptor == "NETFLIX"
    assert tx.is_synthetic is True

    # Retrieve and verify
    fetched = TransactionRepository.get_by_id(db_session, tx.id)
    assert fetched is not None
    assert fetched.amount == Decimal("649.00")
    assert fetched.external_synthetic_id == "SYN_TX_001"


def test_foreign_key_enforcement(db_session: Session):
    """Verify that referencing a nonexistent user_id violates foreign key constraint."""
    fake_user_id = uuid.uuid4()
    with pytest.raises(IntegrityError):
        AccountRepository.create(
            db_session,
            user_id=fake_user_id,
            label="Orphan Account",
        )
    db_session.rollback()


def test_unique_constraint_enforcement(db_session: Session):
    """Verify that duplicate (user_id, external_synthetic_id) violates uniqueness constraint."""
    user = UserRepository.create(
        db_session,
        workspace_key=f"ws_uq_{uuid.uuid4().hex[:8]}",
    )
    now_utc = datetime.now(timezone.utc)

    # First transaction with external_synthetic_id
    TransactionRepository.create(
        db_session,
        user_id=user.id,
        external_synthetic_id="DUPLICATE_ID",
        raw_descriptor="SPOTIFY INDIA",
        amount=Decimal("119.00"),
        transaction_date=now_utc,
    )

    # Attempt second transaction with same user and same external_synthetic_id
    with pytest.raises(IntegrityError):
        TransactionRepository.create(
            db_session,
            user_id=user.id,
            external_synthetic_id="DUPLICATE_ID",
            raw_descriptor="SPOTIFY INDIA REPEAT",
            amount=Decimal("119.00"),
            transaction_date=now_utc,
        )
    db_session.rollback()


def test_merchant_persistence(db_session: Session):
    """Verify canonical merchant record creation and retrieval."""
    canonical_name = f"Spotify_{uuid.uuid4().hex[:6]}"
    merchant = MerchantRepository.create(
        db_session,
        canonical_name=canonical_name,
        category="entertainment",
        commitment_type_default="subscription",
    )
    assert merchant.id is not None
    assert merchant.canonical_name == canonical_name
    assert merchant.is_fictional_demo_merchant is True

    fetched = MerchantRepository.get_by_canonical_name(db_session, canonical_name)
    assert fetched is not None
    assert fetched.id == merchant.id
