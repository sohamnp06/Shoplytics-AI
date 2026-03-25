from sqlalchemy import create_engine
from config import DB_URL

# Create engine ONCE (best practice)
engine = create_engine(DB_URL)

def load_data(df, mode="replace"):

    try:
        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists=mode,   # "replace" for batch, "append" for real-time
            index=False
        )

        print(f"[LOAD] Data loaded into PostgreSQL (mode={mode})")

    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        raise