from sqlalchemy import create_engine
from config import DB_URL, CLEANED_DATA_PATH
import os
import pandas as pd
import stat
import time

engine = create_engine(DB_URL)

def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _try_clear_readonly(path: str) -> None:
    try:
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
    except Exception:
        # Best-effort only; locking (e.g. Excel) will still fail.
        pass


def _write_csv_with_retries(write_fn, target_path: str, *, retries: int = 6, delay_s: float = 0.5) -> None:
    """
    Windows commonly locks CSVs when opened in Excel, causing PermissionError.
    We retry briefly and then raise a clear error so the UI can instruct the user.
    """
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


def load_data(df, mode="replace"):

    try:
        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists=mode,
            index=False
        )

        print(f"[LOAD] Data loaded into PostgreSQL (mode={mode})")

        if not CLEANED_DATA_PATH:
            raise ValueError("CLEANED_DATA_PATH is not set. Please set it in .env (e.g. data/cleaned_sales.csv).")

        _ensure_parent_dir(CLEANED_DATA_PATH)

        if mode == "replace":
            _write_csv_with_retries(lambda: df.to_csv(CLEANED_DATA_PATH, index=False), CLEANED_DATA_PATH)

        elif mode == "append":
            if os.path.exists(CLEANED_DATA_PATH):
                _write_csv_with_retries(
                    lambda: df.to_csv(CLEANED_DATA_PATH, mode="a", header=False, index=False),
                    CLEANED_DATA_PATH,
                )
            else:
                _write_csv_with_retries(lambda: df.to_csv(CLEANED_DATA_PATH, index=False), CLEANED_DATA_PATH)

        print(f"[LOAD] Data written to CSV at {CLEANED_DATA_PATH}")

    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        raise