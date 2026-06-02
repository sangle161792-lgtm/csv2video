"""
src/engine/validator.py
Validates a pandas DataFrame for use in bar chart race animations.
Returns human-readable warning/error strings.
"""
import pandas as pd
from typing import List, Tuple


def validate(df: pd.DataFrame) -> List[str]:
    """
    Validate DataFrame structure and content.

    Returns:
        List of error/warning strings.  Empty list = all good.
    """
    errors: List[str] = []

    if df is None or df.empty:
        errors.append("❌ File is empty or could not be parsed.")
        return errors

    if len(df.columns) < 2:
        errors.append("❌ Need at least 2 columns: a time column + one data column.")
        return errors

    time_col = df.columns[0]
    data_cols = df.columns[1:]

    # Minimum rows
    if len(df) < 2:
        errors.append("❌ Data must have at least 2 time periods (rows) for animation.")

    # Duplicate time values
    dupes = df[time_col].duplicated().sum()
    if dupes:
        errors.append(f"⚠️  Found {dupes} duplicate value(s) in time column '{time_col}'.")

    # Non-numeric data columns
    non_numeric = []
    for col in data_cols:
        try:
            pd.to_numeric(df[col], errors="raise")
        except (ValueError, TypeError):
            non_numeric.append(col)
    if non_numeric:
        errors.append(f"❌ Non-numeric data in column(s): {', '.join(non_numeric)}")

    # Missing values
    missing = int(df[data_cols].isnull().sum().sum())
    if missing:
        errors.append(f"⚠️  {missing} missing value(s) found — they will be treated as 0.")

    # Completely empty rows
    empty_rows = int(df.isnull().all(axis=1).sum())
    if empty_rows:
        errors.append(f"⚠️  {empty_rows} completely empty row(s) — they will be ignored.")

    return errors


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and normalise the DataFrame so the renderer can use it directly.
    - Drops fully-empty rows
    - Coerces all data columns to float (NaN → 0)
    - Resets index
    """
    if df is None or df.empty:
        return df

    df = df.dropna(how="all").copy()
    data_cols = df.columns[1:]
    for col in data_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df.reset_index(drop=True)
