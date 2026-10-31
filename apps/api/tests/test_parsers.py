"""Tests for file parsers, column mapping, schema normalization, and file validation."""
import io
import json
import pytest
from app.ingestion.column_mapper import ColumnMapper
from app.ingestion.csv_parser import CSVParser
from app.ingestion.file_validator import FileValidator
from app.ingestion.json_parser import JSONParser
from app.ingestion.schema_normalizer import SchemaNormalizer
from app.ingestion.xlsx_parser import XLSXParser
import pandas as pd


def test_file_validator_rules():
    """Verify size limits, file types, and synthetic confirmation."""
    # 1. Reject without synthetic confirmation
    res_no_conf = FileValidator.validate_upload("test.csv", b"Date,Amount\n2026-05-01,100", synthetic_confirmed=False)
    assert not res_no_conf.is_valid
    assert "synthetic demo data" in res_no_conf.error_message.lower()

    # 2. Reject empty file
    res_empty = FileValidator.validate_upload("empty.csv", b"", synthetic_confirmed=True)
    assert not res_empty.is_valid
    assert "empty" in res_empty.error_message.lower()

    # 3. Reject unsupported extension
    res_bad_ext = FileValidator.validate_upload("report.pdf", b"%PDF-1.5...", synthetic_confirmed=True)
    assert not res_bad_ext.is_valid
    assert "unsupported" in res_bad_ext.error_message.lower()

    # 4. Reject oversized file (> 10MB)
    oversized = b"0" * (10 * 1024 * 1024 + 1)
    res_oversized = FileValidator.validate_upload("large.csv", oversized, synthetic_confirmed=True)
    assert not res_oversized.is_valid
    assert "exceeds" in res_oversized.error_message.lower()

    # 5. Accept valid file
    res_ok = FileValidator.validate_upload("valid.csv", b"Date,Description,Amount\n2026-05-01,Test,100", synthetic_confirmed=True)
    assert res_ok.is_valid
    assert res_ok.checksum_sha256 != ""


def test_column_mapper_autodetection():
    """Verify auto-detection works with varied header aliases."""
    headers = ["Txn Date", "Narration", "Debit Amount", "Payment Mode", "UTR"]
    mapping = ColumnMapper.auto_detect(headers)

    assert mapping["transaction_date"] == "Txn Date"
    assert mapping["raw_descriptor"] == "Narration"
    assert mapping["amount"] == "Debit Amount"
    assert mapping["payment_channel"] == "Payment Mode"
    assert mapping["payment_reference"] == "UTR"

    # Validate mapping passes
    errors = ColumnMapper.validate_mapping(mapping, headers)
    assert len(errors) == 0


def test_csv_parser_and_schema_normalizer():
    """Verify CSV parsing and transaction normalization."""
    csv_bytes = b"Date,Description,Amount,Channel\n2026-05-10,StreamPulse Sub,499.00,upi\n2026-05-12,Zenith Fitness,2499.00,card\n"
    headers, rows = CSVParser.parse(csv_bytes)

    assert headers == ["Date", "Description", "Amount", "Channel"]
    assert len(rows) == 2

    mapping = ColumnMapper.auto_detect(headers)
    norm = SchemaNormalizer.normalize_transactions(rows, mapping)

    assert len(norm.valid_records) == 2
    assert len(norm.errors) == 0
    assert norm.valid_records[0]["amount"] == 499.00
    assert norm.valid_records[0]["raw_descriptor"] == "StreamPulse Sub"
    assert norm.valid_records[0]["payment_channel"] == "upi"


def test_schema_normalizer_row_errors():
    """Verify invalid rows produce detailed RowErrors without crashing."""
    bad_rows = [
        {"_row_number": 1, "Date": "not-a-date", "Description": "Test A", "Amount": "100.00"},
        {"_row_number": 2, "Date": "2026-05-01", "Description": "", "Amount": "200.00"},
        {"_row_number": 3, "Date": "2026-05-01", "Description": "Test C", "Amount": "abc_not_number"},
    ]
    mapping = {"transaction_date": "Date", "raw_descriptor": "Description", "amount": "Amount"}
    norm = SchemaNormalizer.normalize_transactions(bad_rows, mapping)

    assert len(norm.valid_records) == 0
    assert len(norm.errors) == 3

    assert norm.errors[0].row == 1
    assert "Invalid date" in norm.errors[0].reason

    assert norm.errors[1].row == 2
    assert "Description cannot be empty" in norm.errors[1].reason

    assert norm.errors[2].row == 3
    assert "Invalid numeric amount" in norm.errors[2].reason


def test_xlsx_parser():
    """Verify Excel parsing extracts headers and rows."""
    df = pd.DataFrame([
        {"Date": "2026-06-01", "Description": "Excel Merchant", "Amount": 799.00},
        {"Date": "2026-06-02", "Description": "Excel Merchant 2", "Amount": 1299.00},
    ])
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    xlsx_bytes = buf.getvalue()

    headers, rows = XLSXParser.parse(xlsx_bytes)
    assert "Date" in headers
    assert "Description" in headers
    assert len(rows) == 2
    assert rows[0]["Description"] == "Excel Merchant"


def test_json_notification_parser_and_normalizer():
    """Verify JSON parsing and notification schema validation."""
    notifs = [
        {
            "external_synthetic_id": "NOTIF-001",
            "event_timestamp": "2026-05-01T10:00:00Z",
            "event_type": "mandate_created",
            "merchant_hint": "StreamPulse",
            "amount": 499.00,
            "message_text": "Mandate created for StreamPulse",
        }
    ]
    json_bytes = json.dumps(notifs).encode("utf-8")
    headers, rows = JSONParser.parse(json_bytes)

    assert len(rows) == 1
    norm = SchemaNormalizer.normalize_notifications(rows)
    assert len(norm.valid_records) == 1
    assert norm.valid_records[0]["external_synthetic_id"] == "NOTIF-001"
    assert norm.valid_records[0]["event_type"] == "mandate_created"
