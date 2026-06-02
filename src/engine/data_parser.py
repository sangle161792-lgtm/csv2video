"""
src/engine/data_parser.py
Parses CSV and JSON files into pandas DataFrames.
"""
import pandas as pd
from typing import Optional


def parse_csv(path: str) -> pd.DataFrame:
    """Read a CSV file and return a clean DataFrame."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
    return df


def parse_json(path: str) -> pd.DataFrame:
    """
    Read a JSON file and return a DataFrame.
    Supports both array-of-objects and columnar formats.
    """
    df = pd.read_json(path)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def load_file(path: str) -> pd.DataFrame:
    """
    Dispatch to the correct parser based on file extension.
    Raises ValueError for unsupported extensions.
    """
    lower = path.lower()
    if lower.endswith(".csv"):
        return parse_csv(path)
    elif lower.endswith(".json"):
        return parse_json(path)
    else:
        raise ValueError(f"Unsupported file type. Use .csv or .json  (got: {path})")
