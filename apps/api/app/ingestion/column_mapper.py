"""Column mapping and auto-detection for statement ingestion."""
from typing import Dict, List, Optional, Set


class ColumnMapper:
    """Detects and maps source headers to standard internal transaction schema."""

    TARGET_COLUMNS = [
        "transaction_date",
        "raw_descriptor",
        "amount",
        "currency",
        "direction",
        "payment_channel",
        "payment_reference",
        "external_synthetic_id",
    ]

    REQUIRED_TARGETS: Set[str] = {"transaction_date", "raw_descriptor", "amount"}

    ALIASES: Dict[str, List[str]] = {
        "transaction_date": [
            "date",
            "transaction_date",
            "txn_date",
            "value_date",
            "posting_date",
            "trans_date",
            "txn date",
            "transaction date",
            "trans date",
        ],
        "raw_descriptor": [
            "description",
            "raw_descriptor",
            "narration",
            "particulars",
            "merchant",
            "details",
            "remarks",
            "transaction_details",
            "narrative",
            "payee",
        ],
        "amount": [
            "amount",
            "debit",
            "withdrawal",
            "withdrawal_amount",
            "debit_amount",
            "txn_amount",
            "transaction_amount",
            "net amount",
            "amt",
        ],
        "currency": ["currency", "curr", "ccy"],
        "direction": ["direction", "type", "dr_cr", "cr_dr", "txn_type"],
        "payment_channel": ["channel", "payment_channel", "mode", "payment_mode", "instrument"],
        "payment_reference": ["reference", "ref", "payment_reference", "ref_no", "reference_number", "utr", "cheque_no"],
        "external_synthetic_id": ["external_synthetic_id", "external_id", "synthetic_id", "id", "txn_id", "transaction_id"],
    }

    @classmethod
    def auto_detect(cls, headers: List[str]) -> Dict[str, str]:
        """Automatically map source headers to standard target fields."""
        mapping: Dict[str, str] = {}  # target_field -> source_header
        assigned_sources: Set[str] = set()

        # Clean source headers for comparison
        cleaned_headers = {h: h.strip().lower().replace("_", "").replace(" ", "").replace("-", "") for h in headers}

        for target, aliases in cls.ALIASES.items():
            for alias in aliases:
                norm_alias = alias.lower().replace("_", "").replace(" ", "").replace("-", "")
                for orig_h, clean_h in cleaned_headers.items():
                    if orig_h not in assigned_sources and clean_h == norm_alias:
                        mapping[target] = orig_h
                        assigned_sources.add(orig_h)
                        break
                if target in mapping:
                    break

        return mapping

    @classmethod
    def apply_overrides(
        cls,
        detected_mapping: Dict[str, str],
        user_overrides: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Merge auto-detected mapping with user-supplied column mappings."""
        final_mapping = dict(detected_mapping)
        if user_overrides:
            for target, source in user_overrides.items():
                if source:
                    final_mapping[target] = source
                elif target in final_mapping:
                    del final_mapping[target]
        return final_mapping

    @classmethod
    def validate_mapping(cls, mapping: Dict[str, str], available_headers: List[str]) -> List[str]:
        """Check whether required target columns are mapped to valid available headers."""
        errors: List[str] = []
        for req in cls.REQUIRED_TARGETS:
            if req not in mapping or not mapping[req]:
                errors.append(f"Missing required column mapping for '{req}'.")
            elif mapping[req] not in available_headers:
                errors.append(f"Mapped header '{mapping[req]}' for '{req}' not found in file headers.")
        return errors

