"""JSON notification file parser."""
import json
from typing import Any, Dict, List, Tuple


class JSONParser:
    """Parses raw JSON bytes into records."""

    @staticmethod
    def parse(content: bytes) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Parse JSON bytes into structured rows."""
        try:
            data = json.loads(content.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Invalid JSON syntax: {str(e)}")

        if isinstance(data, dict):
            # If wrapper dictionary like {"notifications": [...]}
            if "notifications" in data and isinstance(data["notifications"], list):
                items = data["notifications"]
            elif "data" in data and isinstance(data["data"], list):
                items = data["data"]
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            raise ValueError("Root JSON must be an array of objects or an object containing an array.")

        rows: List[Dict[str, Any]] = []
        all_keys = set()

        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"Row {idx} is not a valid JSON object.")
            cleaned_item = dict(item)
            cleaned_item["_row_number"] = idx
            rows.append(cleaned_item)
            all_keys.update(k for k in item.keys() if not k.startswith("_"))

        headers = sorted(list(all_keys))
        return headers, rows

