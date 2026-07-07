"""Quick sync check: PostgreSQL vs CSV files."""
from sqlalchemy import text
import pandas as pd
from config import engine, RAW_DATA_PATH, CLEANED_DATA_PATH

with engine.connect() as conn:
    pg_count = conn.execute(text("SELECT COUNT(*) FROM sales_data")).scalar()
    latest = conn.execute(
        text('SELECT "Order_ID", "Date" FROM sales_data ORDER BY "Date" DESC NULLS LAST LIMIT 5')
    ).fetchall()

print("PostgreSQL sales_data count:", pg_count)
print("Latest 5 in PostgreSQL:")
for row in latest:
    print(" ", row)

raw = pd.read_csv(RAW_DATA_PATH)
cleaned = pd.read_csv(CLEANED_DATA_PATH) if __import__("os").path.exists(CLEANED_DATA_PATH) else None

print(f"\n{RAW_DATA_PATH} count:", len(raw))
if len(raw) > 0:
    print("Latest raw Order_ID:", raw["Order_ID"].iloc[-1])

if cleaned is not None:
    print(f"{CLEANED_DATA_PATH} count:", len(cleaned))
    print("Latest cleaned Order_ID:", cleaned["Order_ID"].iloc[-1])

    in_pg = {r[0] for r in latest}
    in_cleaned = set(cleaned["Order_ID"].tail(10).astype(str))
    missing = in_pg - in_cleaned
    if missing:
        print("\nIn PostgreSQL but NOT in cleaned CSV tail:", missing)
