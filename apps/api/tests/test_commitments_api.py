"""Integration tests for commitment discovery, review endpoints, and idempotency."""
import uuid
from decimal import Decimal
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.generators.config import GeneratorConfig
from app.generators.transaction_generator import generate_transactions
from app.matching.reprocessor import TransactionReprocessor
from app.matching.seed_merchants import seed_canonical_merchants
from app.models.account import Account
from app.models.commitment import Commitment
from app.models.demo_user import DemoUser
from app.models.transaction import Transaction
from app.repositories.user_repository import UserRepository


def _setup_demo_data_and_matching(db: Session) -> DemoUser:
    """Helper to seed merchants, aliases, demo user, accounts, and resolved transactions."""
    seed_canonical_merchants(db)
    user = UserRepository.get_or_create_demo_user(db)

    # Create demo account
    account = Account(
        id=uuid.uuid4(),
        user_id=user.id,
        label="Primary Checking",
        account_type="savings",
        currency="INR",
    )
    db.add(account)
    db.commit()

    # Generate synthetic transactions
    fake = Faker()
    cfg = GeneratorConfig(seed=42)
    raw_txns = generate_transactions(cfg, fake)

    tx_models = []
    for t in raw_txns:
        tx_models.append(
            Transaction(
                id=uuid.uuid4(),
                user_id=user.id,
                account_id=account.id,
                external_synthetic_id=t["external_synthetic_id"],
                transaction_date=t["transaction_date"],
                raw_descriptor=t["raw_descriptor"],
                normalised_descriptor=t["normalised_descriptor"],
                amount=Decimal(str(t["amount"])),
                currency=t["currency"],
                direction=t["direction"],
                transaction_status=t["transaction_status"],
                payment_channel=t["payment_channel"],
                payment_reference=t["payment_reference"],
                is_synthetic=True,
            )
        )

    db.add_all(tx_models)
    db.commit()

    # Reprocess transactions to match merchants
    TransactionReprocessor.reprocess(db, user_id=user.id)
    return user


def test_commitment_discovery_lifecycle(client: TestClient, db_session: Session):
    """Verify discovery, detail, timeline, user actions, and discovery idempotency."""
    user = _setup_demo_data_and_matching(db_session)

    # 1. Run discovery
    res = client.post("/api/v1/commitments/discover")
    assert res.status_code == 200
    disc_data = res.json()
    assert disc_data["total_discovered"] >= 10
    assert disc_data["active_count"] >= 8
    assert disc_data["candidate_count"] >= 1

    # 2. List commitments
    list_res = client.get("/api/v1/commitments")
    assert list_res.status_code == 200
    commitments = list_res.json()
    assert len(commitments) == disc_data["total_discovered"]

    # Locate key commitments
    by_name = {c["display_name"]: c for c in commitments}
    assert "StreamPulse Entertainment" in by_name
    sp = by_name["StreamPulse Entertainment"]
    assert sp["cadence"] == "monthly"
    assert sp["commitment_type"] == "subscription"
    assert sp["amount_pattern"] == "fixed"
    assert float(sp["representative_amount"]) == 499.00
    assert sp["status"] == "active"
    assert sp["confidence_band"] == "high"

    # CloudDesk Pro (variable price hike)
    assert "CloudDesk Pro" in by_name
    cd = by_name["CloudDesk Pro"]
    assert cd["cadence"] == "variable_monthly"
    assert cd["amount_pattern"] == "variable"
    assert float(cd["amount_min"]) == 799.00
    assert float(cd["amount_max"]) == 999.00

    # Zenith Fitness Club (membership)
    assert "Zenith Fitness Club" in by_name
    zf = by_name["Zenith Fitness Club"]
    assert zf["commitment_type"] == "membership"
    assert zf["cadence"] == "monthly"

    # FiberNet Broadband (utility with variable amounts)
    assert "FiberNet Broadband" in by_name
    fb = by_name["FiberNet Broadband"]
    assert fb["commitment_type"] == "utility"
    assert fb["cadence"] == "variable_monthly"
    assert fb["amount_pattern"] == "variable"

    # Suraksha General Insurance (single annual candidate)
    assert "Suraksha General Insurance" in by_name
    sg = by_name["Suraksha General Insurance"]
    assert sg["status"] == "candidate"
    assert sg["cadence"] == "annual"
    assert sg["confidence_band"] == "low"
    assert "SINGLE_ANNUAL_OBSERVATION_REQUIRES_MORE_EVIDENCE" in sg["detection_reason_codes"]

    # AquaPure Springs (irregular)
    assert "AquaPure Springs" in by_name
    ap = by_name["AquaPure Springs"]
    assert ap["cadence"] == "irregular"

    # 3. Filter by cadence
    filter_res = client.get("/api/v1/commitments?cadence=irregular")
    assert filter_res.status_code == 200
    irreg_list = filter_res.json()
    assert len(irreg_list) >= 1
    assert any(c["display_name"] == "AquaPure Springs" for c in irreg_list)

    # 4. Search by display name
    search_res = client.get("/api/v1/commitments?search=StreamPulse")
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    # 5. Summary metrics
    sum_res = client.get("/api/v1/commitments/summary")
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_commitments"] == disc_data["total_discovered"]
    assert summary["active_commitments"] >= 8
    assert float(summary["total_monthly_spend"]) > 0
    assert "monthly" in summary["by_cadence"]

    # 6. Commitment Detail and Transactions
    sp_id = sp["id"]
    detail_res = client.get(f"/api/v1/commitments/{sp_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == sp_id
    assert len(detail["supporting_transactions"]) == 6

    tx_res = client.get(f"/api/v1/commitments/{sp_id}/transactions")
    assert tx_res.status_code == 200
    assert len(tx_res.json()) == 6

    # 7. Commitment Timeline
    tl_res = client.get(f"/api/v1/commitments/{sp_id}/timeline")
    assert tl_res.status_code == 200
    tl = tl_res.json()
    assert tl["commitment_id"] == sp_id
    assert len(tl["events"]) >= 6

    # 8. User Confirmation
    confirm_res = client.post(f"/api/v1/commitments/{sp_id}/confirm")
    assert confirm_res.status_code == 200
    confirmed = confirm_res.json()
    assert confirmed["user_decision"] == "confirmed"
    assert confirmed["status"] == "user_confirmed"

    # 9. User Correction (PATCH)
    cd_id = cd["id"]
    patch_res = client.patch(
        f"/api/v1/commitments/{cd_id}",
        json={
            "display_name": "CloudDesk Pro SaaS",
            "commitment_type": "subscription",
            "cadence": "monthly",
        },
    )
    assert patch_res.status_code == 200
    patched = patch_res.json()
    assert patched["display_name"] == "CloudDesk Pro SaaS"
    assert patched["user_decision"] == "corrected"

    # 10. Mark not recurring
    ap_id = ap["id"]
    not_rec_res = client.post(f"/api/v1/commitments/{ap_id}/mark-not-recurring")
    assert not_rec_res.status_code == 200
    not_rec = not_rec_res.json()
    assert not_rec["user_decision"] == "not_recurring"
    assert not_rec["status"] == "marked_not_recurring"

    # 11. IDEMPOTENCY VERIFICATION
    # Running discovery a second time must NOT duplicate commitments
    # and must NOT overwrite user decisions!
    disc_res_2 = client.post("/api/v1/commitments/discover")
    assert disc_res_2.status_code == 200
    assert disc_res_2.json()["total_discovered"] == disc_data["total_discovered"]

    # Verify user decisions remain intact
    list_res_2 = client.get("/api/v1/commitments")
    assert list_res_2.status_code == 200
    by_id_2 = {c["id"]: c for c in list_res_2.json()}

    # StreamPulse must still be user_confirmed
    assert by_id_2[sp_id]["user_decision"] == "confirmed"
    assert by_id_2[sp_id]["status"] == "user_confirmed"

    # CloudDesk Pro must still have corrected display_name
    assert by_id_2[cd_id]["display_name"] == "CloudDesk Pro SaaS"
    assert by_id_2[cd_id]["user_decision"] == "corrected"

    # AquaPure must still be marked_not_recurring
    assert by_id_2[ap_id]["user_decision"] == "not_recurring"
    assert by_id_2[ap_id]["status"] == "marked_not_recurring"
