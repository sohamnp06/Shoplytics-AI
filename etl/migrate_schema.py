"""
migrate_schema.py
-----------------
One-time (or idempotent) migration: fix sales_data column types in PostgreSQL.

Run:
    python -m etl.migrate_schema
"""

from sqlalchemy import text

from config import engine
from utils.logger import setup_logger

logger = setup_logger("etl.migrate")

# Idempotent ALTER statements — safe to run multiple times.
_MIGRATIONS = [
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Is_Returning_Customer" TYPE BOOLEAN
    USING (
        CASE
            WHEN "Is_Returning_Customer" IS NULL THEN FALSE
            WHEN LOWER(TRIM("Is_Returning_Customer"::text)) IN ('true','t','1','yes','y') THEN TRUE
            ELSE FALSE
        END
    );
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Delivery_Time_Days" TYPE DOUBLE PRECISION
    USING NULLIF(TRIM("Delivery_Time_Days"::text), '')::double precision;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Is_Delayed" TYPE INTEGER
    USING COALESCE(NULLIF(TRIM("Is_Delayed"::text), ''), '0')::integer;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Age" TYPE DOUBLE PRECISION
    USING NULLIF(TRIM("Age"::text), '')::double precision;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Unit_Price" TYPE DOUBLE PRECISION
    USING NULLIF(TRIM("Unit_Price"::text), '')::double precision;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Quantity" TYPE DOUBLE PRECISION
    USING NULLIF(TRIM("Quantity"::text), '')::double precision;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Customer_Rating" TYPE DOUBLE PRECISION
    USING NULLIF(TRIM("Customer_Rating"::text), '')::double precision;
    """,
    """
    ALTER TABLE sales_data
    ALTER COLUMN "Date" TYPE DATE
    USING (
        CASE
            WHEN "Date" IS NULL THEN NULL
            WHEN "Date"::text ~ '^[0-9]{2}-[0-9]{2}-[0-9]{4}' THEN to_date("Date"::text, 'DD-MM-YYYY')
            ELSE ("Date"::timestamp)::date
        END
    );
    """,
]


def migrate_schema() -> None:
    """Apply column type fixes so Power BI receives BOOLEAN / numeric types."""
    logger.info("Starting PostgreSQL schema type migration for sales_data...")

    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT EXISTS ("
                "  SELECT 1 FROM information_schema.tables "
                "  WHERE table_name = 'sales_data'"
                ")"
            )
        ).scalar()

        if not exists:
            logger.warning("sales_data table does not exist — nothing to migrate.")
            return

        for sql in _MIGRATIONS:
            try:
                conn.execute(text(sql))
            except Exception as exc:
                err = str(exc).lower()
                if "already" in err or "cannot cast" in err:
                    logger.info("Skipped (already correct or incompatible row): %s", exc)
                else:
                    raise

    logger.info("Schema migration completed successfully.")


if __name__ == "__main__":
    migrate_schema()
