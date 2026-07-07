"""
seed_from_cleaned.py
--------------------
One-off utility that wipes the existing 'sales_data' table in PostgreSQL
and reloads it fresh from the cleaned CSV.

Run with:
    python -m etl.seed_from_cleaned
or directly:
    python etl/seed_from_cleaned.py
"""

import pandas as pd
from sqlalchemy import text

from config import CLEANED_DATA_PATH, engine
from utils.logger import setup_logger

logger = setup_logger("etl.seed")


def seed():
    logger.info("Starting fresh database seed from cleaned CSV.")

    logger.info("Reading CSV: %s", CLEANED_DATA_PATH)
    df = pd.read_csv(CLEANED_DATA_PATH)
    logger.info("Loaded %d rows x %d columns", len(df), len(df.columns))

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS sales_data CASCADE"))
        conn.commit()
    logger.info("Old 'sales_data' table dropped (if it existed)")

    df.to_sql(
        name="sales_data",
        con=engine,
        if_exists="replace",
        index=False,
        chunksize=500,
    )
    logger.info(
        "SUCCESS: %d rows loaded into 'sales_data'. Columns: %s",
        len(df),
        df.columns.tolist(),
    )


if __name__ == "__main__":
    seed()
