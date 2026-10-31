"""Export synthetic datasets to CSV, XLSX, and JSON."""
import json
from pathlib import Path
from typing import Any, Dict, List
import pandas as pd


def export_dataset(dataset: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
    """Export transactions and notifications into standard files in output_dir."""
    output_dir.mkdir(parents=True, exist_ok=True)

    transactions: List[Dict[str, Any]] = dataset["transactions"]
    notifications: List[Dict[str, Any]] = dataset["notifications"]
    manifest: Dict[str, Any] = dataset["manifest"]

    # 1. Prepare bank statement DataFrame
    statement_rows = []
    for t in transactions:
        statement_rows.append({
            "Date": t["date"],
            "Description": t["raw_descriptor"],
            "Amount": t["amount"],
            "Currency": t["currency"],
            "Direction": t["direction"],
            "Channel": t["payment_channel"],
            "Reference": t["payment_reference"],
            "External_ID": t["external_synthetic_id"],
        })

    df = pd.DataFrame(statement_rows)

    # File paths
    csv_path = output_dir / "synthetic_bank_statement.csv"
    xlsx_path = output_dir / "synthetic_bank_statement.xlsx"
    json_path = output_dir / "synthetic_payment_notifications.json"
    manifest_path = output_dir / "dataset_manifest.json"

    # Write CSV (UTF-8)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    # Write XLSX (openpyxl)
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    # Write JSON notifications
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(notifications, f, indent=2, ensure_ascii=False)

    # Write JSON manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return {
        "csv": csv_path,
        "xlsx": xlsx_path,
        "notifications_json": json_path,
        "manifest_json": manifest_path,
    }
