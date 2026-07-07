"""Verify PostgreSQL column types for Power BI compatibility."""
from sqlalchemy import text
from config import engine

with engine.connect() as conn:
    rows = conn.execute(
        text(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'sales_data'
              AND column_name IN (
                'Is_Returning_Customer', 'Delivery_Time_Days', 'Is_Delayed',
                'Date', 'Age', 'Unit_Price', 'Quantity'
              )
            ORDER BY column_name
            """
        )
    ).fetchall()

    print("PostgreSQL column types:")
    for name, dtype in rows:
        print(f"  {name}: {dtype}")

    sample = conn.execute(
        text(
            """
            SELECT "Order_ID", "Date", "Is_Returning_Customer", "Delivery_Time_Days"
            FROM sales_data
            ORDER BY "Date" DESC NULLS LAST
            LIMIT 5
            """
        )
    ).fetchall()

print("\nLatest 3 rows (typed values):")
for r in sample:
    print(" ", r)
