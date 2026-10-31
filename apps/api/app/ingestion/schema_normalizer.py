"""Schema normalizer and row validator for transactions and notifications."""
import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from dateutil import parser as date_parser


@dataclass
class RowError:
    """Error encountered during row parsing or validation."""

    row: int
    column: str
    value: Any
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "row": self.row,
            "column": self.column,
            "value": str(self.value) if self.value is not None else "",
            "reason": self.reason,
        }


@dataclass
class NormalizedRowResult:
    """Outcome of schema normalization across a batch of raw records."""

    valid_records: List[Dict[str, Any]]
    errors: List[RowError]
    total_rows: int


class SchemaNormalizer:
    """Normalizes raw input rows into validated domain models with full error tracking."""

    @classmethod
    def normalize_transactions(
        cls,
        rows: List[Dict[str, Any]],
        mapping: Dict[str, str],
    ) -> NormalizedRowResult:
        """Normalize bank statement rows using provided column mapping."""
        valid_records: List[Dict[str, Any]] = []
        errors: List[RowError] = []

        date_col = mapping.get("transaction_date")
        desc_col = mapping.get("raw_descriptor")
        amount_col = mapping.get("amount")
        curr_col = mapping.get("currency")
        dir_col = mapping.get("direction")
        channel_col = mapping.get("payment_channel")
        ref_col = mapping.get("payment_reference")
        ext_id_col = mapping.get("external_synthetic_id")

        for row in rows:
            row_num = row.get("_row_number", 0)
            row_errors: List[RowError] = []

            # 1. Parse Description (Raw Descriptor)
            raw_desc = str(row.get(desc_col, "")).strip() if desc_col else ""
            if not raw_desc:
                row_errors.append(RowError(row_num, desc_col or "raw_descriptor", "", "Description cannot be empty."))

            # 2. Parse Date
            raw_date_val = row.get(date_col)
            parsed_date: Optional[datetime] = None
            if not raw_date_val:
                row_errors.append(RowError(row_num, date_col or "transaction_date", "", "Transaction date cannot be empty."))
            else:
                try:
                    if isinstance(raw_date_val, datetime):
                        parsed_date = raw_date_val
                    else:
                        parsed_date = date_parser.parse(str(raw_date_val))
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                except Exception as e:
                    row_errors.append(RowError(row_num, date_col or "transaction_date", raw_date_val, f"Invalid date: {str(e)}"))

            # 3. Parse Amount
            raw_amount_val = row.get(amount_col)
            parsed_amount: Optional[Decimal] = None
            if raw_amount_val is None or str(raw_amount_val).strip() == "":
                row_errors.append(RowError(row_num, amount_col or "amount", "", "Amount cannot be empty."))
            else:
                try:
                    clean_str = str(raw_amount_val).replace(",", "").replace("₹", "").replace("$", "").strip()
                    parsed_amount = Decimal(clean_str).quantize(Decimal("0.01"))
                    if parsed_amount < 0:
                        # Negative amount signifies debit if not explicitly marked
                        parsed_amount = abs(parsed_amount)
                except (InvalidOperation, ValueError):
                    row_errors.append(RowError(row_num, amount_col or "amount", raw_amount_val, "Invalid numeric amount."))

            # 4. Optional fields
            currency = (str(row.get(curr_col, "INR")).strip().upper() if curr_col and row.get(curr_col) else "INR")
            direction = (str(row.get(dir_col, "debit")).strip().lower() if dir_col and row.get(dir_col) else "debit")
            if direction not in ("debit", "credit"):
                direction = "debit"

            channel = (str(row.get(channel_col, "unknown")).strip().lower() if channel_col and row.get(channel_col) else "unknown")
            reference = (str(row.get(ref_col)).strip() if ref_col and row.get(ref_col) else None)

            # 5. External Synthetic ID
            ext_id = (str(row.get(ext_id_col)).strip() if ext_id_col and row.get(ext_id_col) else None)
            if not ext_id and parsed_date and raw_desc and parsed_amount is not None:
                # Generate stable reproducible synthetic identifier if missing
                h = hashlib.sha256(f"{parsed_date.isoformat()}_{raw_desc}_{parsed_amount}_{row_num}".encode()).hexdigest()[:12]
                ext_id = f"SYN-IMP-{h}"

            if row_errors:
                errors.extend(row_errors)
            else:
                valid_records.append({
                    "transaction_date": parsed_date,
                    "raw_descriptor": raw_desc,
                    "normalised_descriptor": raw_desc.strip(),
                    "amount": parsed_amount,
                    "currency": currency,
                    "direction": direction,
                    "transaction_status": "successful",
                    "payment_channel": channel,
                    "payment_reference": reference,
                    "external_synthetic_id": ext_id,
                    "source_row_number": row_num,
                    "raw_source_snapshot": {k: v for k, v in row.items() if not k.startswith("_")},
                    "is_synthetic": True,
                })

        return NormalizedRowResult(
            valid_records=valid_records,
            errors=errors,
            total_rows=len(rows),
        )

    @classmethod
    def normalize_notifications(
        cls,
        rows: List[Dict[str, Any]],
    ) -> NormalizedRowResult:
        """Normalize payment notification rows with full schema validation."""
        valid_records: List[Dict[str, Any]] = []
        errors: List[RowError] = []

        for row in rows:
            row_num = row.get("_row_number", 0)
            row_errors: List[RowError] = []

            # 1. External Synthetic ID
            ext_id = str(row.get("external_synthetic_id", "")).strip()
            if not ext_id:
                row_errors.append(RowError(row_num, "external_synthetic_id", "", "External synthetic ID is required."))

            # 2. Event Timestamp
            raw_ts = row.get("event_timestamp")
            parsed_ts: Optional[datetime] = None
            if not raw_ts:
                row_errors.append(RowError(row_num, "event_timestamp", "", "Event timestamp is required."))
            else:
                try:
                    if isinstance(raw_ts, datetime):
                        parsed_ts = raw_ts
                    else:
                        parsed_ts = date_parser.parse(str(raw_ts))
                    if parsed_ts.tzinfo is None:
                        parsed_ts = parsed_ts.replace(tzinfo=timezone.utc)
                except Exception as e:
                    row_errors.append(RowError(row_num, "event_timestamp", raw_ts, f"Invalid timestamp: {str(e)}"))

            # 3. Event Type
            event_type = str(row.get("event_type", "")).strip()
            if not event_type:
                row_errors.append(RowError(row_num, "event_type", "", "Event type is required."))

            # 4. Message Text
            message_text = str(row.get("message_text", "")).strip()
            if not message_text:
                row_errors.append(RowError(row_num, "message_text", "", "Message text is required."))

            # 5. Optional amount
            raw_amount = row.get("amount")
            parsed_amount: Optional[Decimal] = None
            if raw_amount is not None and str(raw_amount).strip() != "":
                try:
                    parsed_amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
                except (InvalidOperation, ValueError):
                    row_errors.append(RowError(row_num, "amount", raw_amount, "Invalid numeric amount in notification."))

            merchant_hint = str(row.get("merchant_hint")).strip() if row.get("merchant_hint") else None
            currency = str(row.get("currency", "INR")).strip().upper() if row.get("currency") else "INR"
            mechanism = str(row.get("payment_mechanism")).strip() if row.get("payment_mechanism") else None
            mandate_ref = str(row.get("mandate_external_ref")).strip() if row.get("mandate_external_ref") else None

            if row_errors:
                errors.extend(row_errors)
            else:
                valid_records.append({
                    "external_synthetic_id": ext_id,
                    "event_timestamp": parsed_ts,
                    "event_type": event_type,
                    "merchant_hint": merchant_hint,
                    "amount": parsed_amount,
                    "currency": currency,
                    "payment_mechanism": mechanism,
                    "mandate_external_ref": mandate_ref,
                    "message_text": message_text,
                    "raw_payload": {k: v for k, v in row.items() if not k.startswith("_")},
                    "source_row_number": row_num,
                    "is_synthetic": True,
                })

        return NormalizedRowResult(
            valid_records=valid_records,
            errors=errors,
            total_rows=len(rows),
        )
