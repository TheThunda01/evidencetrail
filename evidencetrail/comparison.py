"""Compare reviewer tables without resolving disagreements or inferring evidence.

Rows are matched only by a complete, unique key. All row numbers refer to the
spreadsheet position, with the header on row 1. Text comparisons ignore outer
whitespace but preserve case and the distinction between evidence statuses.
"""

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

import pandas as pd

from .audit import MAX_COLUMNS, MAX_ROWS, cell_text, normalize_headers

DEFAULT_KEYS = ("report_id", "field")
ISSUE_COLUMNS = ("side", "row_numbers", "reason", "key")


@dataclass
class ComparisonResult:
    """Matched and unmatched records, excluded rows, and their counts."""

    pairs: pd.DataFrame
    issues: pd.DataFrame
    summary: dict[str, int]

    def to_frame(self) -> pd.DataFrame:
        """Return an independent copy of the comparison records."""
        return self.pairs.copy(deep=True)


def _columns(columns: Sequence[str], label: str, *, required: bool = False) -> tuple[str, ...]:
    if isinstance(columns, str):
        raise ValueError(f"Provide {label} as a sequence of column names.")
    names = tuple(columns)
    if (required and not names) or any(not isinstance(name, str) or not name.strip() for name in names):
        raise ValueError(f"{label.capitalize()} must contain nonempty column names.")
    if len(set(names)) != len(names):
        raise ValueError(f"{label.capitalize()} must not contain duplicate names.")
    return names


def _key_text(key: tuple[str, ...]) -> str:
    return json.dumps(key, ensure_ascii=False, separators=(",", ":"))


def compare_tables(
    left: pd.DataFrame,
    right: pd.DataFrame,
    key_columns: Sequence[str] = DEFAULT_KEYS,
    compare_columns: Sequence[str] = ("value", "evidence_status"),
    provenance_columns: Sequence[str] = ("source_locator",),
) -> ComparisonResult:
    """Compare unique keys; exclude ambiguous keys on both sides.

    ``Agreement`` describes the compared fields only. A source-locator change
    is recorded separately and does not demonstrate agreement about source
    support. Missing or duplicated keys are never paired automatically.
    """
    keys = _columns(key_columns, "key columns", required=True)
    compared = _columns(compare_columns, "comparison columns", required=True)
    provenance = _columns(provenance_columns, "provenance columns")
    if set(compared) & set(provenance):
        raise ValueError("Comparison and provenance columns must be distinct.")
    value_columns = tuple(dict.fromkeys(("record_id", *compared, *provenance)))
    output_columns = [*keys, "left_row", "right_row"]
    output_columns.extend(f"{side}_{column}" for column in value_columns for side in ("left", "right"))
    output_columns.extend(("status", "different_fields", "locator_diff"))
    if len(output_columns) != len(set(output_columns)):
        raise ValueError("Key columns conflict with reserved comparison output names.")
    required_columns = tuple(dict.fromkeys((*keys, *value_columns)))
    if {"_row", "_key"} & set(required_columns):
        raise ValueError("The names _row and _key are reserved for comparison metadata.")
    sides: dict[str, list[dict]] = {}
    groups: dict[str, dict[tuple[str, ...], list[dict]]] = {}
    issues: list[dict] = []
    blocked: dict[str, set[int]] = {"left": set(), "right": set()}

    for side, frame in (("left", left), ("right", right)):
        if not isinstance(frame, pd.DataFrame):
            raise ValueError(f"The {side} table must be a pandas DataFrame.")
        if len(frame) > MAX_ROWS or len(frame.columns) > MAX_COLUMNS:
            raise ValueError(f"The {side} table exceeds the limit of {MAX_ROWS:,} rows or {MAX_COLUMNS} columns.")
        headers = normalize_headers(list(frame.columns))
        missing = [column for column in required_columns if column not in headers]
        if missing:
            raise ValueError(f"Missing required columns in the {side} table: " + ", ".join(missing) + ".")
        positions = {column: headers.index(column) for column in required_columns}
        rows = []
        by_key: dict[tuple[str, ...], list[dict]] = defaultdict(list)
        for number, values in enumerate(frame.itertuples(index=False, name=None), start=2):
            row = {column: cell_text(values[position]) for column, position in positions.items()}
            row["_row"] = number
            row["_key"] = tuple(row[column] for column in keys)
            rows.append(row)
            if not all(row["_key"]):
                blocked[side].add(number)
                issues.append({"side": side, "row_numbers": str(number), "reason": "Missing key", "key": _key_text(row["_key"])})
            else:
                by_key[row["_key"]].append(row)
        sides[side], groups[side] = rows, by_key

    duplicate_keys = {key for by_key in groups.values() for key, rows in by_key.items() if len(rows) > 1}
    for side in ("left", "right"):
        for key, rows in groups[side].items():
            if key not in duplicate_keys:
                continue
            blocked[side].update(row["_row"] for row in rows)
            issues.append({
                "side": side,
                "row_numbers": ", ".join(str(row["_row"]) for row in rows),
                "reason": "Duplicate key" if len(rows) > 1 else "Counterpart has duplicate key",
                "key": _key_text(key),
            })

    available = {
        side: {row["_key"]: row for row in rows if row["_row"] not in blocked[side]}
        for side, rows in sides.items()
    }
    pairs: list[dict] = []

    def add_pair(first: dict | None, second: dict | None) -> None:
        source = first if first is not None else second
        result = {column: source[column] for column in keys}
        result.update(left_row=first["_row"] if first else None, right_row=second["_row"] if second else None)
        for column in value_columns:
            result[f"left_{column}"] = first[column] if first else ""
            result[f"right_{column}"] = second[column] if second else ""
        differences = [column for column in compared if first[column] != second[column]] if first and second else []
        result["status"] = ("Difference" if differences else "Agreement") if first and second else ("Left only" if first else "Right only")
        result["different_fields"] = ", ".join(differences)
        result["locator_diff"] = bool(first and second and any(first[column] != second[column] for column in provenance))
        pairs.append(result)

    for key, row in available["left"].items():
        add_pair(row, available["right"].get(key))
    for key, row in available["right"].items():
        if key not in available["left"]:
            add_pair(None, row)
    paired = pd.DataFrame(pairs, columns=output_columns)
    paired["left_row"] = pd.array(paired["left_row"], dtype="Int64")
    paired["right_row"] = pd.array(paired["right_row"], dtype="Int64")
    paired["locator_diff"] = paired["locator_diff"].astype(bool)
    counts = paired["status"].value_counts()
    summary = {
        "comparable_pairs": int(counts.get("Agreement", 0) + counts.get("Difference", 0)),
        "agreements": int(counts.get("Agreement", 0)),
        "differences": int(counts.get("Difference", 0)),
        "left_only": int(counts.get("Left only", 0)),
        "right_only": int(counts.get("Right only", 0)),
        "blocked_rows": sum(len(numbers) for numbers in blocked.values()),
    }
    issues.sort(key=lambda issue: (0 if issue["side"] == "left" else 1, int(issue["row_numbers"].split(",")[0])))
    return ComparisonResult(paired, pd.DataFrame(issues, columns=ISSUE_COLUMNS), summary)


def comparison_id(
    left_sha: str,
    right_sha: str,
    left_sheet: str | None = None,
    right_sheet: str | None = None,
    left_mapping: Mapping | None = None,
    right_mapping: Mapping | None = None,
    key_columns: Sequence[str] | None = None,
) -> str:
    """Identify a comparison's source bytes, sheets, mappings, and match keys.

    The digest identifies inputs, not scientific validity. Switching inputs or
    their interpretation produces a different identifier for decision state.
    """
    if not isinstance(left_sha, str) or not left_sha.strip() or not isinstance(right_sha, str) or not right_sha.strip():
        raise ValueError("Both source hashes are required.")
    keys = _columns(DEFAULT_KEYS if key_columns is None else key_columns, "key columns", required=True)
    payload = {
        "version": 1, "left_sha": left_sha.strip(), "right_sha": right_sha.strip(),
        "left_sheet": left_sheet, "right_sheet": right_sheet,
        "left_mapping": dict(left_mapping or {}), "right_mapping": dict(right_mapping or {}),
        "key_columns": list(keys),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
