"""
load.py
-------
Handles all write operations:
  - load_data()       → PostgreSQL + cleaned CSV  (batch replace or append)
  - append_raw_csv()  → raw source file           (pre-transformation append)
"""

import os
import stat
import time

import pandas as pd
from sqlalchemy import text

from config import CLEANED_DATA_PATH, RAW_DATA_PATH, engine
from etl.dtypes import PG_DTYPES, coerce_dataframe_for_pg, parse_bool
from utils.logger import setup_logger

logger = setup_logger("etl.load")

_RAW_COLUMNS = [
    "Order_ID", "Customer_ID", "Date", "Age", "Gender", "City",
    "Product_Category", "Unit_Price", "Quantity", "Discount_Amount",
    "Total_Amount", "Payment_Method", "Device_Type",
    "Session_Duration_Minutes", "Pages_Viewed",
    "Is_Returning_Customer", "Delivery_Time_Days", "Customer_Rating",
]


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _try_clear_readonly(path: str) -> None:
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
    except OSError:
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


def sync_cleaned_csv_from_db() -> None:
    """Rebuild cleaned CSV from PostgreSQL so it matches the database exactly.

    Used as a fallback when incremental CSV append fails (e.g. file open in Excel)
    and to keep Power BI CSV sources in sync with PostgreSQL.
    """
    if not CLEANED_DATA_PATH:
        logger.warning("CLEANED_DATA_PATH not set — skipping CSV sync.")
        return

    try:
        _ensure_parent_dir(CLEANED_DATA_PATH)
        with engine.connect() as conn:
            df = pd.read_sql(text('SELECT * FROM sales_data'), conn)

        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

        _write_csv_with_retries(
            lambda: df.to_csv(CLEANED_DATA_PATH, index=False),
            CLEANED_DATA_PATH,
        )
        logger.info(
            "Synced cleaned CSV from PostgreSQL -> %s (%d rows)",
            CLEANED_DATA_PATH,
            len(df),
        )

    except Exception as e:
        logger.error("Cleaned CSV sync from PostgreSQL failed: %s", e)
        raise


def append_raw_csv(data: dict) -> None:
    """Append a single raw record to the raw source CSV (pre-transformation).

    Real-time form submissions are always written as CSV rows so the batch
    pipeline can reload the full dataset (including web entries) on demand.
    """
    raw_csv_path = RAW_DATA_PATH
    if raw_csv_path.lower().endswith((".xlsx", ".xls")):
        raw_csv_path = str(
            os.path.join(os.path.dirname(raw_csv_path), "raw_sales.csv")
        )

    if not raw_csv_path:
        logger.warning("RAW_DATA_PATH not set — skipping raw CSV append.")
        return

    try:
        row = {col: data.get(col, "") for col in _RAW_COLUMNS}
        # Normalise bool for raw CSV consistency (True/False, not "1"/"0")
        if "Is_Returning_Customer" in row:
            row["Is_Returning_Customer"] = parse_bool(row["Is_Returning_Customer"])
        df_raw = pd.DataFrame([row])

        _ensure_parent_dir(raw_csv_path)

        if os.path.exists(raw_csv_path):
            _write_csv_with_retries(
                lambda: df_raw.to_csv(raw_csv_path, mode="a", header=False, index=False),
                raw_csv_path,
            )
        else:
            _write_csv_with_retries(
                lambda: df_raw.to_csv(raw_csv_path, index=False),
                raw_csv_path,
            )

        logger.info("Raw record appended to %s", raw_csv_path)

    except Exception as e:
        logger.error("Raw CSV append failed: %s", e)
        raise


def load_data(df: pd.DataFrame, mode: str = "replace") -> None:
    """Write transformed DataFrame to PostgreSQL and cleaned CSV.

    PostgreSQL is the primary target. CSV export is best-effort on append.
    """
    df = coerce_dataframe_for_pg(df)

    try:
        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists=mode,
            index=False,
            dtype=PG_DTYPES,
        )
        logger.info("PostgreSQL write OK (mode=%s, rows=%d)", mode, len(df))

    except Exception as e:
        logger.error("PostgreSQL write failed: %s", e)
        raise

    if not CLEANED_DATA_PATH:
        logger.warning("CLEANED_DATA_PATH not set — skipping CSV export.")
        return

    df_csv = df.copy()
    if "Date" in df_csv.columns:
        df_csv["Date"] = pd.to_datetime(df_csv["Date"], errors="coerce").dt.strftime("%Y-%m-%d")

    try:
        _ensure_parent_dir(CLEANED_DATA_PATH)

        if mode == "replace":
            _write_csv_with_retries(
                lambda: df_csv.to_csv(CLEANED_DATA_PATH, index=False),
                CLEANED_DATA_PATH,
            )
        elif mode == "append":
            if os.path.exists(CLEANED_DATA_PATH):
                _write_csv_with_retries(
                    lambda: df_csv.to_csv(
                        CLEANED_DATA_PATH, mode="a", header=False, index=False
                    ),
                    CLEANED_DATA_PATH,
                )
            else:
                _write_csv_with_retries(
                    lambda: df_csv.to_csv(CLEANED_DATA_PATH, index=False),
                    CLEANED_DATA_PATH,
                )

        logger.info("Cleaned CSV write OK -> %s", CLEANED_DATA_PATH)

    except PermissionError as e:
        logger.warning(
            "Cleaned CSV append failed (file likely open in Excel): %s. "
            "Rebuilding cleaned CSV from PostgreSQL.",
            e,
        )
        try:
            sync_cleaned_csv_from_db()
        except Exception as sync_err:
            logger.error(
                "PostgreSQL write succeeded but cleaned CSV sync also failed: %s",
                sync_err,
            )
            raise PermissionError(
                f"PostgreSQL updated but cleaned CSV could not be synced. "
                f"Close '{CLEANED_DATA_PATH}' in Excel, then retry."
            ) from sync_err
    except Exception as e:
        logger.error("Cleaned CSV write failed: %s", e)
        raise
