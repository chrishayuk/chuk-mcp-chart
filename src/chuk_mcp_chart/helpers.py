"""Parsing and normalisation helpers for chart data.

Handles the many creative ways LLMs format labels, datasets, CSV, and JSON
so the tool layer can stay clean and focused on chart construction.
"""

import csv
import io
import json
from typing import Any, Optional

from chuk_view_schemas.chart import ChartContent, ChartDataset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHART_TYPE_ALIASES = {
    "polar": "radar",
    "polar area": "radar",
}

DEFAULT_COLOURS = [
    "#3b82f6",  # blue
    "#ef4444",  # red
    "#22c55e",  # green
    "#f59e0b",  # amber
    "#8b5cf6",  # violet
    "#06b6d4",  # cyan
    "#ec4899",  # pink
    "#64748b",  # slate
    "#14b8a6",  # teal
    "#f97316",  # orange
]


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def resolve_chart_type(raw: str) -> str:
    """Normalise user-supplied chart type string."""
    key = raw.strip().lower()
    return CHART_TYPE_ALIASES.get(key, key)


def assign_colours(datasets: list[dict]) -> list[dict]:
    """Assign default colours to datasets that don't have one."""
    for i, ds in enumerate(datasets):
        if not ds.get("color"):
            ds["color"] = DEFAULT_COLOURS[i % len(DEFAULT_COLOURS)]
    return datasets


def is_numeric(value: str) -> bool:
    """Check if a string can be parsed as a number."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_labeled_value(v: Any) -> bool:
    """Check if a value is already a ``{"label": ..., "value": ...}`` dict."""
    return isinstance(v, dict) and "label" in v and "value" in v


# ---------------------------------------------------------------------------
# Label parsing
# ---------------------------------------------------------------------------
def parse_labels(raw: str) -> list[str]:
    """Parse labels from either a JSON array string or comma-separated string.

    LLMs send both ``"A,B,C"`` and ``'["A","B","C"]'`` — handle either.
    """
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed]
        except json.JSONDecodeError:
            pass
    return [item.strip() for item in raw.split(",")]


# ---------------------------------------------------------------------------
# Dataset normalisation
# ---------------------------------------------------------------------------
def normalise_dataset(ds: dict) -> dict:
    """Normalise LLM variations in dataset keys.

    Handles:
    - ``"data"`` → ``"values"``
    - ``"backgroundColor"`` → ``"color"``
    - ``"borderColor"`` → ``"color"`` (if color not already set)
    """
    if "data" in ds and "values" not in ds:
        ds["values"] = ds.pop("data")
    if "backgroundColor" in ds and "color" not in ds:
        ds["color"] = ds.pop("backgroundColor")
    elif "backgroundColor" in ds:
        ds.pop("backgroundColor")
    if "borderColor" in ds and "color" not in ds:
        ds["color"] = ds.pop("borderColor")
    elif "borderColor" in ds:
        ds.pop("borderColor")
    return ds


def build_values(raw_values: list, labels: list[str]) -> list:
    """Build chart values, handling all LLM variations.

    Accepts:
    - Plain numbers: ``[10, 20, 30]``
    - Pre-structured LabeledValue dicts: ``[{"label":"A","value":10}]``
    - Mixed lists
    """
    if not raw_values:
        return []

    # Already-structured — pass through
    if all(is_labeled_value(v) for v in raw_values):
        return raw_values

    result = []
    for idx, val in enumerate(raw_values):
        if is_labeled_value(val):
            result.append(val)
        else:
            lbl = labels[idx] if idx < len(labels) else f"Item {idx + 1}"
            try:
                result.append({"label": lbl, "value": float(val)})
            except (ValueError, TypeError):
                result.append({"label": lbl, "value": 0})
    return result


def parse_datasets(raw: Optional[str]) -> list[dict]:
    """Parse and normalise a JSON datasets string.

    Tolerant of:
    - A JSON array of objects  (standard)
    - A single JSON object     (auto-wrapped)
    - ``None`` / empty string  (returns placeholder)
    """
    if not raw:
        return [{"label": "Data", "values": []}]

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"datasets must be a valid JSON array: {exc}") from exc

    if isinstance(parsed, dict):
        return [parsed]
    if not isinstance(parsed, list):
        raise ValueError("datasets must be a JSON array of objects.")

    return list(parsed)


# ---------------------------------------------------------------------------
# CSV → ChartContent
# ---------------------------------------------------------------------------
def parse_csv(raw_csv: str) -> tuple[list[str], list[list[str]]]:
    """Parse CSV text into a header row and data rows."""
    reader = csv.reader(io.StringIO(raw_csv.strip()))
    rows = list(reader)
    if len(rows) < 2:
        raise ValueError("CSV must have at least a header row and one data row.")
    header = [h.strip() for h in rows[0]]
    data_rows = rows[1:]
    return header, data_rows


def csv_to_chart_content(
    header: list[str],
    data_rows: list[list[str]],
    chart_type: str,
    title: Optional[str],
) -> ChartContent:
    """Convert parsed CSV columns into a ChartContent model.

    Heuristic:
    - First non-numeric column becomes labels.
    - Each remaining numeric column becomes a dataset.
    - If ALL columns are numeric, use row indices as labels.
    """
    ct = resolve_chart_type(chart_type)

    numeric_cols: list[int] = []
    label_col: Optional[int] = None

    for col_idx in range(len(header)):
        col_values = [row[col_idx] for row in data_rows if col_idx < len(row)]
        if all(is_numeric(v) for v in col_values if v.strip()):
            numeric_cols.append(col_idx)
        elif label_col is None:
            label_col = col_idx

    if not numeric_cols:
        raise ValueError("CSV must contain at least one numeric column for chart values.")

    if label_col is not None:
        labels = [row[label_col].strip() for row in data_rows if label_col < len(row)]
    else:
        labels = [str(i + 1) for i in range(len(data_rows))]

    datasets: list[dict] = []
    for col_idx in numeric_cols:
        col_name = header[col_idx] if col_idx < len(header) else f"Series {col_idx}"
        values = []
        for row_idx, row in enumerate(data_rows):
            lbl = labels[row_idx] if row_idx < len(labels) else str(row_idx + 1)
            if col_idx < len(row) and row[col_idx].strip():
                values.append({"label": lbl, "value": float(row[col_idx])})
            else:
                values.append({"label": lbl, "value": 0})
        datasets.append({"label": col_name, "values": values})

    datasets = assign_colours(datasets)

    return ChartContent(
        title=title or "Chart",
        chart_type=ct,
        data=[ChartDataset(**ds) for ds in datasets],
    )


# ---------------------------------------------------------------------------
# JSON array → ChartContent
# ---------------------------------------------------------------------------
def json_to_chart_content(
    data: list[dict],
    chart_type: str,
    title: Optional[str],
) -> ChartContent:
    """Convert a JSON array of objects into a ChartContent model.

    Heuristic: first string field → labels, numeric fields → datasets.
    """
    ct = resolve_chart_type(chart_type)
    if not data:
        raise ValueError("JSON array must not be empty.")

    first = data[0]
    label_key: Optional[str] = None
    numeric_keys: list[str] = []

    for key, value in first.items():
        if isinstance(value, (int, float)):
            numeric_keys.append(key)
        elif isinstance(value, str) and label_key is None:
            label_key = key

    if not numeric_keys:
        raise ValueError("JSON objects must contain at least one numeric field for chart values.")

    if label_key:
        labels = [str(obj.get(label_key, f"Row {i + 1}")) for i, obj in enumerate(data)]
    else:
        labels = [str(i + 1) for i in range(len(data))]

    datasets: list[dict] = []
    for nk in numeric_keys:
        values = []
        for i, obj in enumerate(data):
            lbl = labels[i]
            val = obj.get(nk, 0)
            values.append({"label": lbl, "value": float(val) if val is not None else 0})
        datasets.append({"label": nk, "values": values})

    datasets = assign_colours(datasets)

    return ChartContent(
        title=title or "Chart",
        chart_type=ct,
        data=[ChartDataset(**ds) for ds in datasets],
    )
