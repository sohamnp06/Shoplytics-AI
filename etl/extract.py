"""
extract.py
----------
Extract raw sales data from Excel (.xlsx) or CSV (.csv).

The file path is read from RAW_DATA_PATH in config.py.
If the configured path does not exist, common fallbacks are tried automatically.
"""

import os
from pathlib import Path

import pandas as pd

from config import DATA_DIR, RAW_DATA_PATH
from utils.logger import setup_logger

logger = setup_logger("etl.extract")

# Ordered fallback list — first existing file wins.
_FALLBACK_PATHS = [
    RAW_DATA_PATH,
    str(DATA_DIR / "raw_sales.xlsx"),
    str(DATA_DIR / "raw_sales.csv"),
    str(DATA_DIR / "SalesData.csv"),
    str(DATA_DIR / "SalesData.xlsx"),
]


def _resolve_source_path() -> str:
    """Return the first existing raw-data file from configured or fallback paths."""
    seen = set()
    for path in _FALLBACK_PATHS:
        if not path or path in seen:
            continue
        seen.add(path)
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        "No raw data file found. Set RAW_DATA_PATH in .env or place a file at "
        f"{DATA_DIR / 'raw_sales.xlsx'} or {DATA_DIR / 'SalesData.csv'}."
    )


def _read_file(path: str) -> pd.DataFrame:
    """Read Excel or CSV based on file extension."""
    ext = Path(path).suffix.lower()

    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path, engine="openpyxl")
        logger.info("Read Excel source: %s", path)
    elif ext == ".csv":
        df = pd.read_csv(path)
        logger.info("Read CSV source: %s", path)
    else:
        raise ValueError(
            f"Unsupported file type '{ext}' for '{path}'. Use .xlsx, .xls, or .csv."
        )

    return df


def extract_data() -> pd.DataFrame:
    """Load raw sales data into a Pandas DataFrame."""
    try:
        source_path = _resolve_source_path()
        df = _read_file(source_path)

        logger.info("Extracted shape: %s", df.shape)
        logger.info("Columns: %s", df.columns.tolist())

        return df

    except Exception as e:
        logger.error("Extract failed: %s", e)
        raise
