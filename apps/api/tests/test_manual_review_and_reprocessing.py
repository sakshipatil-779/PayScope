"""Integration tests for manual review workflows, import auto-matching, and reprocessing."""
import io
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.matching.seed_merchants import seed_canonical_merchants
from app.models.audit_event import AuditEvent
from app.models.demo_user import DemoUser
from app.models.descriptor_alias import DescriptorAlias
from app.models.manual_review_item import ManualReviewItem
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.repositories.user_repository import UserRepository


@pytest.fixture(autouse=True)
def seed_test_database(db_session: Session):
    """Seed test database with canonical merchants and aliases before tests."""
    seed_canonical_merchants(db_session)


def test_automatic_resolution_during_import(client: TestClient, db_session: Session):
    """Uploaded statement transactions must be automatically resolved against the merchant database."""
    csv_content = (
        b"Date,Description,Amount,Channel,External_ID\n"
        b"2026-05-01,UPI/STREAMPULSE/BILLPAY/982138,499.00,upi,SYN-IMP-RES-01\n"
        b"2026-05-02,RAZORPAY*MERCH_INTL_4819,850.00,upi,SYN-IMP-RES-02\n"
    )

    res = client.post(
        "/api/v1/imports",
        files={"file": ("statement.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "true"},
    )
    assert res.status_code == 201

    txns = list(db_session.scalars(select(Transaction).order_by(Transaction.transaction_date.asc())).all())
    assert len(txns) == 2

    # First txn: StreamPulse Entertainment (exact alias match)
    t1 = txns[0]
    assert t1.merchant_id is not None
    assert t1.merchant.canonical_name == "StreamPulse Entertainment"
    assert t1.merchant_match_status == "matched"
    assert t1.merchant_match_confidence == "high"

    # Second txn: Ambiguous aggregator (Scenario 12)
    t2 = txns[1]
    assert t2.merchant_match_status == "needs_review"

    # Verify manual review queue received the item
    reviews = list(db_session.scalars(select(ManualReviewItem)).all())
    assert len(reviews) == 1
    assert reviews[0].raw_descriptor == "RAZORPAY*MERCH_INTL_4819"
    assert reviews[0].status == "open"


def test_manual_review_accept_action(client: TestClient, db_session: Session):
    """Accepting a review suggestion confirms the merchant and records an audit event."""
    user = UserRepository.get_or_create_demo_user(db_session)
    merchant = db_session.scalar(select(Merchant).where(Merchant.canonical_name == "CloudDesk Pro"))

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    txn = Transaction(
        user_id=user.id,
        raw_descriptor="RAZORPAY*CLOUDDESK BLR",
        normalised_descriptor="razorpay clouddesk blr",
        amount=799.00,
        transaction_date=now,
        merchant_match_status="needs_review",
        is_synthetic=True,
    )
    db_session.add(txn)
    db_session.flush()

    item = ManualReviewItem(
        user_id=user.id,
        transaction_id=txn.id,
        item_type="merchant_match",
        raw_descriptor=txn.raw_descriptor,
        normalised_descriptor=txn.normalised_descriptor,
        suggested_merchant_id=merchant.id,
        status="open",
        reason_code="low_confidence",
    )
    db_session.add(item)
    db_session.commit()

    # Call Accept API
    res = client.post(f"/api/v1/merchant-reviews/{item.id}/accept")
    assert res.status_code == 200
    assert res.json()["status"] == "accepted"

    # Verify transaction is confirmed
    db_session.refresh(txn)
    assert txn.merchant_id == merchant.id
    assert txn.merchant_match_status == "user_confirmed"

    # Verify AuditEvent
    audits = list(db_session.scalars(select(AuditEvent)).all())
    assert any(a.action == "manual_review_accepted" for a in audits)


def test_manual_review_correct_action_with_alias_creation(client: TestClient, db_session: Session):
    """Correcting review to another merchant creates alias and confirms transaction."""
    user = UserRepository.get_or_create_demo_user(db_session)
    merchants = list(db_session.scalars(select(Merchant)).all())
    m1 = merchants[0]
    m2 = merchants[1]

    from datetime import datetime, timezone
    txn = Transaction(
        user_id=user.id,
        raw_descriptor="CUSTOM DESCRIPTOR UNKNOWN",
        normalised_descriptor="custom descriptor unknown",
        amount=1200.00,
        transaction_date=datetime.now(timezone.utc),
        merchant_match_status="needs_review",
        is_synthetic=True,
    )
    db_session.add(txn)
    db_session.flush()

    item = ManualReviewItem(
        user_id=user.id,
        transaction_id=txn.id,
        item_type="merchant_match",
        raw_descriptor=txn.raw_descriptor,
        normalised_descriptor=txn.normalised_descriptor,
        suggested_merchant_id=m1.id,
        status="open",
        reason_code="ambiguous",
    )
    db_session.add(item)
    db_session.commit()

    # Correct to m2 with create_alias=True
    res = client.post(
        f"/api/v1/merchant-reviews/{item.id}/correct",
        json={"merchant_id": str(m2.id), "create_alias": True, "decision_notes": "Identified as m2"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "corrected"
    assert data["alias_created"] is True

    # Verify new alias created for m2
    new_alias = db_session.scalar(
        select(DescriptorAlias).where(
            DescriptorAlias.merchant_id == m2.id,
            DescriptorAlias.alias_text == "CUSTOM DESCRIPTOR UNKNOWN",
        )
    )
    assert new_alias is not None
    assert new_alias.is_active is True

    # Verify transaction updated
    db_session.refresh(txn)
    assert txn.merchant_id == m2.id
    assert txn.merchant_match_status == "user_confirmed"


def test_reprocessing_idempotence_and_preserves_user_confirmations(client: TestClient, db_session: Session):
    """Reprocessing must be idempotent and NEVER overwrite user_confirmed decisions."""
    user = UserRepository.get_or_create_demo_user(db_session)
    merchants = list(db_session.scalars(select(Merchant)).all())
    confirmed_merchant = merchants[0]

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    # 1. User confirmed transaction (should NEVER be changed by reprocessing)
    txn_confirmed = Transaction(
        user_id=user.id,
        raw_descriptor="SPECIAL OVERRIDE DESCRIPTOR",
        normalised_descriptor="special override descriptor",
        amount=500.00,
        transaction_date=now,
        merchant_id=confirmed_merchant.id,
        merchant_match_status="user_confirmed",
        merchant_match_method="user_confirmed",
        is_synthetic=True,
    )

    # 2. Unmatched transaction for StreamPulse
    txn_unmatched = Transaction(
        user_id=user.id,
        raw_descriptor="POS STRMPLSE INTL BLR",
        normalised_descriptor="pos strmplse intl blr",
        amount=499.00,
        transaction_date=now,
        merchant_match_status="unmatched",
        is_synthetic=True,
    )

    db_session.add_all([txn_confirmed, txn_unmatched])
    db_session.commit()

    # Trigger Reprocessing API
    res = client.post("/api/v1/merchants/reprocess-unmatched")
    assert res.status_code == 200
    report = res.json()
    assert report["matched_count"] >= 1
    assert report["skipped_user_confirmed_count"] >= 1

    # Verify txn_confirmed was untouched
    db_session.refresh(txn_confirmed)
    assert txn_confirmed.merchant_id == confirmed_merchant.id
    assert txn_confirmed.merchant_match_status == "user_confirmed"
    assert txn_confirmed.raw_descriptor == "SPECIAL OVERRIDE DESCRIPTOR"

    # Verify txn_unmatched was resolved to StreamPulse
    db_session.refresh(txn_unmatched)
    assert txn_unmatched.merchant is not None
    assert txn_unmatched.merchant.canonical_name == "StreamPulse Entertainment"
    assert txn_unmatched.merchant_match_status == "matched"
