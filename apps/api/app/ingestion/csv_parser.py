"""CSV file parser with encoding and delimiter auto-detection."""
import csv
import io
from typing import Any, Dict, List, Tuple


class CSVParser:
    """Parses raw CSV bytes into column headers and row dictionaries."""

    @staticmethod
    def parse(content: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Decode and parse CSV content."""
        # Try UTF-8-sig (handles UTF-8 with BOM), fallback to UTF-8, then latin-1
        text = None
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                text = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError("Unable to decode CSV file with supported encodings (UTF-8, Latin-1).")

        # Detect delimiter using Sniffer, fallback to comma
        sample = text[:4096]
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=",\t;|")
        except Exception:
            dialect = csv.excel

        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        headers = [h.strip() for h in (reader.fieldnames or []) if h is not None]
        rows: List[Dict[str, Any]] = []

        for row_idx, row in enumerate(reader, start=1):
            cleaned_row = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items() if k is not None}
            cleaned_row["_row_number"] = row_idx
            rows.append(cleaned_row)

        return headers, rows
