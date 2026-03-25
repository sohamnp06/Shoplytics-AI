from sqlalchemy import create_engine
from config import DB_URL, CLEANED_DATA_PATH
import os
import pandas as pd

engine = create_engine(DB_URL)


def load_data(df, mode="replace"):

    try:
        # -------------------------
        # 1. LOAD TO POSTGRESQL
        # -------------------------
        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists=mode,
            index=False
        )

        print(f"[LOAD] Data loaded into PostgreSQL (mode={mode})")

        # -------------------------
        # 2. LOAD TO CSV (IMPORTANT)
        # -------------------------
        if mode == "replace":
            # Batch → overwrite CSV
            df.to_csv(CLEANED_DATA_PATH, index=False)

        elif mode == "append":
            # Real-time → append to CSV
            if os.path.exists(CLEANED_DATA_PATH):
                df.to_csv(CLEANED_DATA_PATH, mode='a', header=False, index=False)
            else:
                df.to_csv(CLEANED_DATA_PATH, index=False)

        print(f"[LOAD] Data written to CSV at {CLEANED_DATA_PATH}")

    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        raise