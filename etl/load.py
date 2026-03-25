from sqlalchemy import create_engine
from config import DB_CONFIG

def load_data(df):

    try:
        engine = create_engine(
            f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )

        df.to_sql(
            name="sales_data",
            con=engine,
            if_exists="replace",   
            index=False
        )

        print("[LOAD] Data loaded into PostgreSQL")

    except Exception as e:
        print(f"[LOAD ERROR] {e}")
        raise