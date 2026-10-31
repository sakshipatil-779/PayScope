"""End-to-end integration tests for Phase 6 commitment insights API."""
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from faker import Faker
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.generators.config import GeneratorConfig
from app.generators.notification_generator import generate_notifications
from app.generators.transaction_generator import generate_transactions
from app.matching.reprocessor import TransactionReprocessor
from app.matching.seed_merchants import seed_canonical_merchants
from app.models.account import Account
from app.models.commitment import Commitment
from app.models.demo_user import DemoUser
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction
from app.repositories.user_repository import UserRepository


def _setup_full_demo_environment(client: TestClient, db: Session) -> DemoUser:
    """Setup full test environment with merchants, transactions, notifications, and commitments."""
    seed_canonical_merchants(db)
    user = UserRepository.get_or_create_demo_user(db)

    account = Account(
        id=uuid.uuid4(),
        user_id=user.id,
        label="Primary Checking",
        account_type="savings",
        currency="INR",
    )
    db.add(account)
    db.commit()

    fake = Faker()
    cfg = GeneratorConfig(seed=42)
    raw_txns = generate_transactions(cfg, fake)

    tx_models = []
    for t in raw_txns:
        tx_dt = t["transaction_date"]
        if isinstance(tx_dt, str):
            tx_dt = datetime.fromisoformat(tx_dt)
        tx_models.append(
            Transaction(
                id=uuid.uuid4(),
                user_id=user.id,
                account_id=account.id,
                external_synthetic_id=t["external_synthetic_id"],
                transaction_date=tx_dt,
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

    # Ingest synthetic notifications
    raw_notifs = generate_notifications(cfg, fake)
    notif_models = []
    for n in raw_notifs:
        ts = n["event_timestamp"]
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        notif_models.append(
            PaymentNotification(
                id=uuid.uuid4(),
                user_id=user.id,
                external_synthetic_id=n["external_synthetic_id"],
                event_timestamp=ts,
                event_type=n["event_type"],
                merchant_hint=n.get("merchant_hint"),
                amount=Decimal(str(n["amount"])) if n.get("amount") is not None else None,
                currency=n.get("currency") or "INR",
                payment_mechanism=n.get("payment_mechanism") or "upi",
                message_text=n.get("message_text", ""),
                raw_payload=n,
            )
        )
    db.add_all(notif_models)
    db.commit()

    # Reprocess transactions to match merchants
    TransactionReprocessor.reprocess(db, user_id=user.id)

    # Run commitment discovery
    res = client.post("/api/v1/commitments/discover")
    assert res.status_code == 200

    return user


def test_insight_detection_and_review_lifecycle(client: TestClient, db_session: Session):
    """Test full Phase 6 lifecycle: detection run, category queries, deep dive, and review actions."""
    user = _setup_full_demo_environment(client, db_session)

    # 1. Run insight detection
    detect_res = client.post("/api/v1/insights/detect")
    assert detect_res.status_code == 200
    det_data = detect_res.json()
    assert det_data["status"] == "completed"
    assert det_data["total_detected"] >= 4
    assert det_data["price_increases_detected"] >= 1
    assert det_data["trial_conversions_detected"] >= 1
    assert det_data["potentially_unused_detected"] >= 1
    assert det_data["post_cancellation_charges_detected"] >= 1

    # 2. Get Insights Summary
    summary_res = client.get("/api/v1/insights/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["total_open"] >= 4
    assert summary["price_increases"] >= 1
    assert summary["trial_conversions"] >= 1
    assert summary["potentially_unused"] >= 1
    assert summary["post_cancellation_charges"] >= 1
    assert float(summary["estimated_monthly_impact"]) > 0

    # 3. Query category convenience endpoints
    # A. Price Changes (CloudDesk Pro)
    pc_res = client.get("/api/v1/insights/price-changes")
    assert pc_res.status_code == 200
    price_insights = pc_res.json()
    assert len(price_insights) >= 1
    cd_insight = next((i for i in price_insights if "CloudDesk" in i["commitment_name"]), None)
    assert cd_insight is not None
    assert cd_insight["insight_type"] == "price_increase"
    assert cd_insight["severity"] == "medium"

    # B. Trial Conversions (SynthWrite AI)
    tc_res = client.get("/api/v1/insights/trial-conversions")
    assert tc_res.status_code == 200
    trial_insights = tc_res.json()
    assert len(trial_insights) >= 1
    sw_insight = next((i for i in trial_insights if "SynthWrite" in i["commitment_name"]), None)
    assert sw_insight is not None

    # C. Potentially Unused (Zenith Fitness Club)
    unused_res = client.get("/api/v1/insights/unused")
    assert unused_res.status_code == 200
    unused_insights = unused_res.json()
    assert len(unused_insights) >= 1
    zf_insight = next((i for i in unused_insights if "Zenith Fitness" in i["commitment_name"]), None)
    assert zf_insight is not None

    # D. Post-Cancellation Charge (SkyVault Backup)
    pcanc_res = client.get("/api/v1/insights/post-cancellation")
    assert pcanc_res.status_code == 200
    post_canc_insights = pcanc_res.json()
    assert len(post_canc_insights) >= 1
    sv_insight = next((i for i in post_canc_insights if "SkyVault" in i["commitment_name"]), None)
    assert sv_insight is not None
    assert sv_insight["severity"] == "high"

    # 4. Deep-dive into an insight (CloudDesk Pro)
    detail_res = client.get(f"/api/v1/insights/{cd_insight['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == cd_insight["id"]
    assert detail["price_event"] is not None
    assert float(detail["price_event"]["previous_amount"]) == 799.00
    assert float(detail["price_event"]["new_amount"]) == 999.00
    assert len(detail["evidence_items"]) >= 2

    # 5. Review action: Acknowledge
    ack_res = client.post(
        f"/api/v1/insights/{cd_insight['id']}/acknowledge",
        json={"notes": "Reviewed and accepted new price"},
    )
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["status"] == "acknowledged"
    assert ack_data["user_action"] == "acknowledged"

    # 6. Review action: Dismiss
    dism_res = client.post(
        f"/api/v1/insights/{sw_insight['id']}/dismiss",
        json={"reason": "Intended to continue paid tier", "notes": "No action needed"},
    )
    assert dism_res.status_code == 200
    dism_data = dism_res.json()
    assert dism_data["status"] == "dismissed"
    assert dism_data["user_action"] == "dismissed"

    # 7. Review action: Resolve
    res_res = client.post(
        f"/api/v1/insights/{sv_insight['id']}/resolve",
        json={"resolution_action": "Dispute lodged with card issuer", "notes": "Refund requested"},
    )
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert res_data["status"] == "resolved"
    assert res_data["user_action"] == "resolved"

    # 8. Query commitment-specific insights endpoint
    comm_insights_res = client.get(f"/api/v1/commitments/{cd_insight['commitment_id']}/insights")
    assert comm_insights_res.status_code == 200
    comm_insights = comm_insights_res.json()
    assert len(comm_insights) >= 1
    assert any(i["id"] == cd_insight["id"] for i in comm_insights)
