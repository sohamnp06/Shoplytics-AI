"""
seed_from_cleaned.py
--------------------
One-off utility that wipes the existing 'sales_data' table in PostgreSQL
and reloads it fresh from data/CleanedSalesData.csv.

Run with:
    python -m etl.seed_from_cleaned
or directly:
    python etl/seed_from_cleaned.py
"""

import pandas as pd
from sqlalchemy import create_engine, text
from config import DB_URL, CLEANED_DATA_PATH


def seed():
    print("\n[SEED] Starting fresh database seed from CleanedSalesData.csv...\n")

    # 1. Read the cleaned CSV
    print(f"[SEED] Reading CSV: {CLEANED_DATA_PATH}")
    df = pd.read_csv(CLEANED_DATA_PATH)
    print(f"[SEED] Loaded {len(df):,} rows × {len(df.columns)} columns")

    # 2. Connect and drop existing table data
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS sales_data CASCADE"))
        conn.commit()
    print("[SEED] Old 'sales_data' table dropped (if it existed)")

    # 3. Load the fresh data  (mode="replace" creates the table fresh)
    df.to_sql(
        name="sales_data",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=500,   # avoids memory spikes for large files
    )
    print(f"[SEED] SUCCESS: {len(df):,} rows loaded into 'sales_data' table successfully")
    print(f"[SEED] Columns in DB: {df.columns.tolist()}\n")


if __name__ == "__main__":
    seed()
