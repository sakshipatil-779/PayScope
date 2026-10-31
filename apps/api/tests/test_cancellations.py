"""Unit and integration tests for Phase 8 Cancellation Centre."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.analytics.cancellations.config import (
    GENERIC_CARD_SI_PLAYBOOK,
    GENERIC_E_NACH_PLAYBOOK,
    GENERIC_OTHER_PLAYBOOK,
    GENERIC_UPI_AUTOPAY_PLAYBOOK,
    VERIFIED_MERCHANT_PLAYBOOKS,
)
from app.analytics.cancellations.friction_analyzer import analyze_cancellation_friction
from app.analytics.cancellations.instruction_builder import build_cancellation_checklist, calculate_progress_percentage
from app.analytics.cancellations.mechanism_classifier import classify_payment_mechanism
from app.analytics.cancellations.playbook_resolver import resolve_playbook
from app.analytics.cancellations.schemas import GuidanceType, PaymentMechanism
from app.models.cancellation_case import CancellationCase
from app.models.cancellation_event import CancellationEvent
from app.models.commitment import Commitment
from app.models.commitment_transaction import CommitmentTransaction
from app.models.demo_user import DemoUser
from app.models.merchant import Merchant
from app.models.transaction import Transaction


@pytest.fixture
def test_user(db_session):
    user = DemoUser(
        id=uuid.uuid4(),
        workspace_key=f"ws_cancel_{uuid.uuid4().hex[:6]}",
        display_name="Cancellation Test User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_user(db_session):
    user = DemoUser(
        id=uuid.uuid4(),
        workspace_key=f"ws_other_{uuid.uuid4().hex[:6]}",
        display_name="Other User",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_merchant(db_session):
    m = Merchant(
        id=uuid.uuid4(),
        canonical_name="Netflix",
        category="Entertainment",
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


@pytest.fixture
def upi_commitment(db_session, test_user, sample_merchant):
    now = datetime.now(timezone.utc)
    comm = Commitment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        merchant_id=sample_merchant.id,
        display_name="Netflix Premium",
        commitment_type="subscription",
        cadence="monthly",
        amount_pattern="fixed",
        representative_amount=Decimal("649.00"),
        first_seen_at=now,
        last_seen_at=now,
        status="active",
        confidence_score=Decimal("0.95"),
    )
    db_session.add(comm)
    db_session.flush()

    tx = Transaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        transaction_date=datetime(2026, 2, 1, 10, 0, tzinfo=timezone.utc),
        raw_descriptor="UPI/NETFLIX/AUTOPAY@HDFC/99281",
        normalised_descriptor="netflix autopay",
        amount=Decimal("649.00"),
        direction="debit",
        payment_channel="UPI",
    )
    db_session.add(tx)
    db_session.flush()

    ct = CommitmentTransaction(
        commitment_id=comm.id,
        transaction_id=tx.id,
        relationship_role="evidence",
    )
    db_session.add(ct)
    db_session.commit()
    db_session.refresh(comm)
    return comm


def test_mechanism_classifier_upi(upi_commitment, db_session):
    txs = list(upi_commitment.transactions or [])
    mechanism, confidence = classify_payment_mechanism(upi_commitment, txs)
    assert mechanism == PaymentMechanism.UPI_AUTOPAY
    assert confidence > 0.5


def test_mechanism_classifier_card_and_nach(db_session, test_user):
    now = datetime.now(timezone.utc)
    comm = Commitment(
        id=uuid.uuid4(),
        user_id=test_user.id,
        display_name="Home Loan EMI",
        status="active",
        cadence="monthly",
        first_seen_at=now,
        last_seen_at=now,
    )
    db_session.add(comm)
    db_session.flush()

    tx_nach = Transaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        transaction_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
        raw_descriptor="ACH/ENACH/HDFC00123/LOAN-MANDATE",
        amount=Decimal("25000.00"),
        direction="debit",
        payment_channel="NACH",
    )
    db_session.add(tx_nach)
    db_session.flush()

    mechanism, _ = classify_payment_mechanism(comm, [tx_nach])
    assert mechanism == PaymentMechanism.E_NACH

    tx_card = Transaction(
        id=uuid.uuid4(),
        user_id=test_user.id,
        transaction_date=datetime(2026, 1, 5, tzinfo=timezone.utc),
        raw_descriptor="POS DEBIT CARD SI NETFLIX",
        amount=Decimal("199.00"),
        direction="debit",
        payment_channel="CARD",
    )
    mechanism_card, _ = classify_payment_mechanism(comm, [tx_card])
    assert mechanism_card == PaymentMechanism.CARD_SI


def test_verified_playbook_resolver():
    pb_netflix = resolve_playbook(PaymentMechanism.CARD_SI, playbook_key="merchant_netflix")
    assert pb_netflix.guidance_type == GuidanceType.MERCHANT_VERIFIED
    assert "https://help.netflix.com" in pb_netflix.official_source_url
    assert pb_netflix.source_verification_date is not None

    # Fallback to generic when unknown merchant
    pb_generic = resolve_playbook(PaymentMechanism.UPI_AUTOPAY)
    assert pb_generic.guidance_type == GuidanceType.GENERIC_MECHANISM
    assert pb_generic.playbook_key == "generic_upi_autopay"


def test_instruction_builder_and_friction():
    checklist = build_cancellation_checklist(GENERIC_UPI_AUTOPAY_PLAYBOOK, ["upi_step_1", "upi_step_2"])
    assert len(checklist) == len(GENERIC_UPI_AUTOPAY_PLAYBOOK.steps)
    assert checklist[0].is_completed is True
    assert checklist[1].is_completed is True
    assert checklist[2].is_completed is False

    progress = calculate_progress_percentage(len(checklist), 2)
    assert progress > 0

    friction = analyze_cancellation_friction(GENERIC_E_NACH_PLAYBOOK)
    assert friction["friction_level"] == "HIGH"
    assert friction["estimated_minutes"] >= 15


def test_cancellation_case_lifecycle_api(client: TestClient, db_session, test_user, upi_commitment):
    # 1. Eligibility check
    res_elig = client.get(f"/api/v1/cancellations/eligibility/{upi_commitment.id}?user_id={test_user.id}")
    assert res_elig.status_code == 200
    elig_data = res_elig.json()
    assert elig_data["commitment_id"] == str(upi_commitment.id)
    assert "recommended_playbook" in elig_data

    # 2. Create cancellation case
    res_create = client.post(
        f"/api/v1/cancellations?user_id={test_user.id}",
        json={"commitment_id": str(upi_commitment.id), "user_notes": "Cancelling due to infrequent usage."},
    )
    assert res_create.status_code == 201
    case_data = res_create.json()
    case_id = case_data["id"]
    assert case_data["status"] == "NOT_STARTED"
    assert case_data["user_notes"] == "Cancelling due to infrequent usage."

    # 3. Start case
    res_start = client.post(f"/api/v1/cancellations/{case_id}/start?user_id={test_user.id}")
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "IN_PROGRESS"

    # 4. Complete step
    res_step = client.post(
        f"/api/v1/cancellations/{case_id}/complete-step?user_id={test_user.id}",
        json={"step_id": case_data["playbook"]["steps"][0]["id"]},
    )
    assert res_step.status_code == 200
    assert case_data["playbook"]["steps"][0]["id"] in res_step.json()["completed_steps"]

    # 5. Report cancelled (distinguishes user reported from verified)
    res_report = client.post(
        f"/api/v1/cancellations/{case_id}/report-cancelled?user_id={test_user.id}",
        json={
            "cancellation_date": datetime.now(timezone.utc).isoformat(),
            "evidence_references": "Cancelled via Netflix app, ref #991823",
        },
    )
    assert res_report.status_code == 200
    reported_data = res_report.json()
    assert reported_data["status"] == "USER_REPORTED_CANCELLED"
    assert reported_data["user_reported_at"] is not None

    # Verify Phase 6 CancellationEvent was linked
    canc_event = db_session.query(CancellationEvent).filter_by(commitment_id=upi_commitment.id).first()
    assert canc_event is not None
    assert canc_event.event_source == "user_recorded"
    assert canc_event.confirmation_type == "user_confirmed"

    # 6. Verify case
    res_verify = client.post(
        f"/api/v1/cancellations/{case_id}/verify?verification_notes=Observed+zero+subsequent+debits+in+April&user_id={test_user.id}"
    )
    assert res_verify.status_code == 200
    verified_data = res_verify.json()
    assert verified_data["status"] == "VERIFIED_CANCELLED"
    assert verified_data["verified_at"] is not None


def test_user_isolation(client: TestClient, db_session, test_user, other_user, upi_commitment):
    # Create case for test_user
    res_create = client.post(
        f"/api/v1/cancellations?user_id={test_user.id}",
        json={"commitment_id": str(upi_commitment.id)},
    )
    assert res_create.status_code == 201
    case_id = res_create.json()["id"]

    # Other user attempts to read or modify test_user's case -> 404
    res_unauth = client.get(f"/api/v1/cancellations/{case_id}?user_id={other_user.id}")
    assert res_unauth.status_code == 404

    res_unauth_step = client.post(
        f"/api/v1/cancellations/{case_id}/start?user_id={other_user.id}"
    )
    assert res_unauth_step.status_code == 404
