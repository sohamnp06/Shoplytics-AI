"""
load.py
-------
Handles all write operations:
  - load_data()       → PostgreSQL + CleanedSalesData.csv  (batch replace or append)
  - append_raw_csv()  → SalesData.csv  (raw record, pre-transformation)
"""

import os
import stat
import time

import pandas as pd
from sqlalchemy import create_engine, Integer, Boolean

from config import DB_URL, CLEANED_DATA_PATH, RAW_DATA_PATH

engine = create_engine(DB_URL)

# Columns that exist in SalesData.csv (raw, before feature engineering)
_RAW_COLUMNS = [
    "Order_ID", "Customer_ID", "Date", "Age", "Gender", "City",
    "Product_Category", "Unit_Price", "Quantity", "Discount_Amount",
    "Total_Amount", "Payment_Method", "Device_Type",
    "Session_Duration_Minutes", "Pages_Viewed",
    "Is_Returning_Customer", "Delivery_Time_Days", "Customer_Rating",
]

# Explicit SQLAlchemy dtype overrides for columns where pandas dtype inference
# is unreliable on single-row DataFrames:
#   Is_Delayed            → was BOOLEAN (pandas bool8 inference), now enforced INTEGER
#   Is_Returning_Customer → stored as BOOLEAN in PostgreSQL
_SQL_DTYPES = {
    "Is_Delayed": Integer(),
    "Is_Returning_Customer": Boolean(),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _try_clear_readonly(path: str) -> None:
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
    except Exception:
        pass


def _write_csv_with_retries(
    write_fn, target_path: str, *, retries: int = 6, delay_s: float = 0.5
) -> None:
    """Retry CSV writes — Windows locks files open in Excel."""
    last_err = None
    for _ in range(max(1, retries)):
        try:
            write_fn()
            return
        except PermissionError as e:
            last_err = e
            _try_clear_readonly(target_path)
            time.sleep(delay_s)

    raise PermissionError(
        f"Permission denied writing '{target_path}'. "
        f"Close any program using it (especially Excel) and try again."
    ) from last_err


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def append_raw_csv(data: dict) -> None:
    """Append a single raw record to SalesData.csv (pre-transformation).

    Only the original input columns are written — no engineered features.
    This preserves the raw data trail exactly as the user entered it.

    Args:
        data: Dict from the Flask form (numeric fields already cast to float).
    """
    if not RAW_DATA_PATH:
        print("[LOAD] RAW_DATA_PATH not set — skipping raw CSV append.")
        return

    try:
        # Pick only the raw columns; fill missing keys with empty string
        row = {col: data.get(col, "") for col in _RAW_COLUMNS}
        df_raw = pd.DataFrame([row])

        _ensure_parent_dir(RAW_DATA_PATH)

        if os.path.exists(RAW_DATA_PATH):
            _write_csv_with_retries(
                lambda: df_raw.to_csv(RAW_DATA_PATH, mode="a", header=False, index=False),
                RAW_DATA_PATH,
            )
        else:
            # First-ever write — include the header
            _write_csv_with_retries(
                lambda: df_raw.to_csv(RAW_DATA_PATH, index=False),
                RAW_DATA_PATH,
            )

        print(f"[LOAD] Raw record appended to {RAW_DATA_PATH}")

    except Exception as e:
        print(f"[LOAD ERROR - RAW CSV] {e}")
        raise


def load_data(df: pd.DataFrame, mode: str = "replace") -> None:
    """Write transformed DataFrame to PostgreSQL and CleanedSalesData.csv.

    PostgreSQL is the primary target and always treated as critical.
    CSV export is best-effort — a locked file raises a WARNING in logs
    but does NOT roll back the successful PostgreSQL write.

    Args:
        df:   Transformed, validated DataFrame.
        mode: 'replace' (batch) or 'append' (real-time single record).
    """
    # ------------------------------------------------------------------
    # Ensure Is_Delayed is int64 before insert.
    # Prevents psycopg2.errors.DatatypeMismatch on single-row DataFrames
    # where SQLAlchemy can incorrectly infer BOOLEAN from a bool8 column.
    # ------------------------------------------------------------------
    if "Is_Delayed" in df.columns:
        df["Is_Delayed"] = df["Is_Delayed"].astype("int64")

    # ── Step A: Write to PostgreSQL (critical — raises on failure) ──────
    try:
        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists=mode,
            index=False,
            dtype=_SQL_DTYPES,
        )
        print(f"[LOAD] PostgreSQL write OK (mode={mode}, rows={len(df)})")

    except Exception as e:
        print(f"[LOAD ERROR - PostgreSQL] {e}")
        raise   # Re-raise: DB failure is critical

    # ── Step B: Write to CleanedSalesData.csv (best-effort) ─────────────
    if not CLEANED_DATA_PATH:
        print("[LOAD WARNING] CLEANED_DATA_PATH not set — skipping CSV export.")
        return

    try:
        _ensure_parent_dir(CLEANED_DATA_PATH)

        if mode == "replace":
            _write_csv_with_retries(
                lambda: df.to_csv(CLEANED_DATA_PATH, index=False),
                CLEANED_DATA_PATH,
            )
        elif mode == "append":
            if os.path.exists(CLEANED_DATA_PATH):
                _write_csv_with_retries(
                    lambda: df.to_csv(CLEANED_DATA_PATH, mode="a", header=False, index=False),
                    CLEANED_DATA_PATH,
                )
            else:
                _write_csv_with_retries(
                    lambda: df.to_csv(CLEANED_DATA_PATH, index=False),
                    CLEANED_DATA_PATH,
                )

        print(f"[LOAD] CleanedSalesData.csv write OK → {CLEANED_DATA_PATH}")

    except PermissionError as e:
        # File is locked (e.g. open in Excel) — log a warning but do NOT fail.
        # PostgreSQL already has the record; CSV can be re-synced later.
        print(
            f"[LOAD WARNING] Could not write CleanedSalesData.csv (file locked): {e}\n"
            f"  → PostgreSQL write succeeded. Close the CSV in Excel and it will "
            f"    update automatically on the next submission."
        )
    except Exception as e:
        print(f"[LOAD ERROR - CSV] {e}")
        raise