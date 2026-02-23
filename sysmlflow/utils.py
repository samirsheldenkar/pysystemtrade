"""
Utility functions for the MLflow export module.
"""

import math
import os
import re
import tempfile
from typing import Optional

import pandas as pd


def sanitise_metric_name(name: str) -> str:
    """Ensure a metric/param name is MLflow-compatible.

    MLflow allows: alphanumerics, underscores, dashes, periods, spaces,
    and slashes.  Max 250 characters.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9_\-./\s]", "_", name)
    return cleaned[:250]


def flatten_dict(
    d: dict,
    parent_key: str = "",
    separator: str = "/",
) -> dict:
    """Flatten a nested dict into a single-level dict with path-style keys.

    Example:
        {"a": {"b": 1, "c": 2}} -> {"a/b": 1, "a/c": 2}
    """
    items: list = []
    for key, value in d.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else str(key)
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def safe_float(value) -> Optional[float]:
    """Convert a value to float, returning None for NaN/Inf/non-numeric."""
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def is_scalar(value) -> bool:
    """Check if a value is a simple scalar suitable for MLflow params."""
    return isinstance(value, (int, float, str, bool))


def dataframe_to_temp_csv(df: pd.DataFrame, name: str) -> str:
    """Write a DataFrame to a temporary CSV file and return the path.

    The caller is responsible for cleanup (or let the OS handle it).
    """
    temp_dir = tempfile.mkdtemp(prefix="sysmlflow_")
    filename = f"{name}.csv"
    filepath = os.path.join(temp_dir, filename)
    df.to_csv(filepath)
    return filepath


def truncate_param_value(value, max_length: int = 500) -> str:
    """Truncate a parameter value to fit MLflow's limit (500 chars)."""
    s = str(value)
    if len(s) > max_length:
        return s[: max_length - 3] + "..."
    return s
