"""Adapt column names explicitly without changing extraction values or rows."""

import pandas as pd

from .audit import MAX_COLUMNS, MAX_ROWS, REQUIRED_COLUMNS, normalize_headers


def _headers(frame: pd.DataFrame) -> list[str]:
    if not isinstance(frame, pd.DataFrame):
        raise ValueError("Provide a pandas DataFrame containing the extraction table.")
    if len(frame) > MAX_ROWS:
        raise ValueError(f"The table has too many records. The limit is {MAX_ROWS:,}.")
    if len(frame.columns) > MAX_COLUMNS:
        raise ValueError(f"The table has too many columns. The limit is {MAX_COLUMNS}.")
    return normalize_headers(list(frame.columns))


def suggest_mapping(frame: pd.DataFrame) -> dict[str, str | None]:
    """Suggest exact canonical headers only; unknown meanings remain unassigned.

    Header whitespace is trimmed as it is during input loading. Capitalization,
    synonyms, and the meaning of cell contents are not inferred.
    """
    headers = _headers(frame)
    return {column: column if column in headers else None for column in REQUIRED_COLUMNS}


def map_columns(frame: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Return a copied table with an explicit canonical-to-source header mapping.

    Each required canonical name must map to a different existing source column.
    Unmapped columns remain in their original positions, provided their names do
    not collide with mapped names. Values, row order, and the index are preserved.
    Neither the input table nor the mapping is modified.
    """
    headers = _headers(frame)
    if not isinstance(mapping, dict):
        raise ValueError("Provide a column mapping with one source column for each required field.")
    unknown = [str(column) for column in mapping if column not in REQUIRED_COLUMNS]
    if unknown:
        raise ValueError("Unknown required-field names in the mapping: " + ", ".join(unknown) + ".")
    missing = [column for column in REQUIRED_COLUMNS
               if column not in mapping or not isinstance(mapping[column], str) or not mapping[column].strip()]
    if missing:
        raise ValueError("Choose a source column for each required field: " + ", ".join(missing) + ".")
    normalized = {column: mapping[column].strip() for column in REQUIRED_COLUMNS}
    nonexistent = [source for source in normalized.values() if source not in headers]
    if nonexistent:
        raise ValueError("Mapped source columns were not found: " + ", ".join(nonexistent) + ".")
    if len(set(normalized.values())) != len(normalized):
        raise ValueError("Each source column can be mapped only once. Choose a different column for each required field.")
    rename = {source: canonical for canonical, source in normalized.items()}
    mapped_headers = [rename.get(header, header) for header in headers]
    collisions = sorted({header for header in mapped_headers if mapped_headers.count(header) > 1})
    if collisions:
        raise ValueError(
            "Mapped names conflict with columns retained from the input: " + ", ".join(collisions)
            + ". Map those existing columns instead, or rename conflicting columns in a separate copy."
        )
    mapped = frame.copy(deep=True)
    mapped.columns = mapped_headers
    return mapped
