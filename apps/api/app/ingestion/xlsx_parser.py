"""Excel XLSX file parser using openpyxl."""
import io
from datetime import date, datetime
from typing import Any, Dict, List, Tuple
import openpyxl


class XLSXParser:
    """Parses raw Excel XLSX bytes into column headers and row dictionaries."""

    @staticmethod
    def parse(content: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Read active sheet of XLSX content."""
        file_obj = io.BytesIO(content)
        try:
            wb = openpyxl.load_workbook(file_obj, data_only=True, read_only=True)
        except Exception as e:
            raise ValueError(f"Failed to read Excel workbook: {str(e)}")

        sheet = wb.active
        if not sheet:
            raise ValueError("Excel file contains no active worksheet.")

        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return [], []

        headers = [str(h).strip() for h in header_row if h is not None]
        if not headers:
            return [], []

        rows: List[Dict[str, Any]] = []
        for row_idx, row_values in enumerate(rows_iter, start=2):
            # Check if entire row is empty
            if all(v is None or str(v).strip() == "" for v in row_values):
                continue

            row_dict: Dict[str, Any] = {"_row_number": row_idx}
            for col_idx, h in enumerate(headers):
                val = row_values[col_idx] if col_idx < len(row_values) else None
                if isinstance(val, (datetime, date)):
                    val = val.isoformat()
                elif isinstance(val, str):
                    val = val.strip()
                row_dict[h] = val

            rows.append(row_dict)

        wb.close()
        return headers, rows

