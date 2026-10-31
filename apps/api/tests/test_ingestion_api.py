"""API integration tests for ingestion, preview, duplicate detection, and demo endpoints."""
import io
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.demo_user import DemoUser
from app.models.import_record import ImportRecord
from app.models.payment_notification import PaymentNotification
from app.models.transaction import Transaction


def test_preview_rejection_without_synthetic_confirmation(client: TestClient):
    """Attempting import preview without explicit synthetic confirmation must return 400."""
    csv_content = b"Date,Description,Amount\n2026-05-01,Test Merchant,500.00\n"
    response = client.post(
        "/api/v1/imports/preview",
        files={"file": ("statement.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "false"},
    )
    assert response.status_code == 400
    assert "Synthetic confirmation is required" in response.json()["detail"]


def test_preview_valid_csv(client: TestClient):
    """Previewing a valid synthetic CSV returns columns, row counts, and sample preview rows."""
    csv_content = b"Date,Description,Amount,Channel,External_ID\n2026-05-01,StreamPulse Sub,499.00,upi,SYN-001\n2026-05-02,Zenith Fitness,2499.00,card,SYN-002\n"
    response = client.post(
        "/api/v1/imports/preview",
        files={"file": ("statement.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "true"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total_rows"] == 2
    assert data["valid_count"] == 2
    assert data["duplicate_count"] == 0
    assert len(data["preview_rows"]) == 2
    assert data["preview_rows"][0]["descriptor"] == "StreamPulse Sub"


def test_execute_import_persistence_and_duplicate_prevention(client: TestClient, db_session: Session):
    """Uploading the same statement file twice must persist first time and detect duplicates on second."""
    csv_content = (
        b"Date,Description,Amount,Channel,External_ID\n"
        b"2026-05-01,StreamPulse Sub,499.00,upi,SYN-DUP-001\n"
        b"2026-05-02,CloudDesk Pro,799.00,card,SYN-DUP-002\n"
    )

    # 1. First import
    res1 = client.post(
        "/api/v1/imports",
        files={"file": ("statement.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "true"},
    )
    assert res1.status_code == 201
    d1 = res1.json()
    assert d1["accepted_count"] == 2
    assert d1["duplicate_count"] == 0
    assert d1["status"] == "completed"

    # Verify transactions in database
    txns = db_session.query(Transaction).all()
    assert len(txns) == 2

    # 2. Second import of same file
    res2 = client.post(
        "/api/v1/imports",
        files={"file": ("statement.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "true"},
    )
    assert res2.status_code == 201
    d2 = res2.json()
    assert d2["accepted_count"] == 0
    assert d2["duplicate_count"] == 2  # Both skipped as duplicates

    # Total transactions in DB should STILL be 2 (no duplicate insertion)
    db_session.expire_all()
    txns_after = db_session.query(Transaction).all()
    assert len(txns_after) == 2


def test_import_json_notifications(client: TestClient, db_session: Session):
    """Importing payment notifications JSON persists records to payment_notifications table."""
    notifs = [
        {
            "external_synthetic_id": "SYN-NOTIF-TEST-1",
            "event_timestamp": "2026-05-01T10:30:00Z",
            "event_type": "mandate_created",
            "merchant_hint": "StreamPulse",
            "amount": 499.00,
            "payment_mechanism": "upi_autopay",
            "mandate_external_ref": "UMN/STRP/2026/0129",
            "message_text": "UPI AutoPay mandate created for StreamPulse.",
        }
    ]
    json_bytes = json.dumps(notifs).encode("utf-8")

    res = client.post(
        "/api/v1/imports",
        files={"file": ("notifications.json", json_bytes, "application/json")},
        data={"import_type": "notifications", "synthetic_confirmed": "true"},
    )
    assert res.status_code == 201
    d = res.json()
    assert d["accepted_count"] == 1
    assert d["duplicate_count"] == 0

    saved_notifs = db_session.query(PaymentNotification).all()
    assert len(saved_notifs) == 1
    assert saved_notifs[0].external_synthetic_id == "SYN-NOTIF-TEST-1"
    assert saved_notifs[0].event_type == "mandate_created"


def test_list_and_get_imports(client: TestClient):
    """Verify listing imports and retrieving single import detail."""
    csv_content = b"Date,Description,Amount\n2026-05-01,Test,100.00\n"
    create_res = client.post(
        "/api/v1/imports",
        files={"file": ("test.csv", csv_content, "text/csv")},
        data={"import_type": "statement", "synthetic_confirmed": "true"},
    )
    assert create_res.status_code == 201
    import_id = create_res.json()["import_id"]

    # List imports
    list_res = client.get("/api/v1/imports")
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    assert len(items) >= 1
    assert items[0]["id"] == import_id

    # Get single import
    get_res = client.get(f"/api/v1/imports/{import_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == import_id

    # Get import status
    status_res = client.get(f"/api/v1/imports/{import_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ("completed", "partially_completed")


def test_demo_sample_files_endpoints(client: TestClient):
    """Verify listing sample files, streaming download, and path traversal rejection."""
    # List
    res_list = client.get("/api/v1/demo/sample-files")
    assert res_list.status_code == 200
    files = res_list.json()
    assert len(files) == 4
    filenames = [f["filename"] for f in files]
    assert "synthetic_bank_statement.csv" in filenames
    assert "synthetic_payment_notifications.json" in filenames

    # Download valid sample file
    res_dl = client.get("/api/v1/demo/sample-files/synthetic_bank_statement.csv")
    assert res_dl.status_code == 200
    assert "Date,Description,Amount" in res_dl.text

    # Path traversal attempt rejected
    res_bad = client.get("/api/v1/demo/sample-files/../../etc/passwd")
    assert res_bad.status_code in (400, 404)


def test_demo_generate_endpoint(client: TestClient):
    """Verify demo generation endpoint triggers with custom seed."""
    res = client.post("/api/v1/demo/generate", json={"seed": 100})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["seed"] == 100
    assert data["manifest"]["summary"]["transaction_count"] >= 80
