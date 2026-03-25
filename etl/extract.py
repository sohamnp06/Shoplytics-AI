import pandas as pd
from config import RAW_DATA_PATH

def extract_data():
    try:
        df = pd.read_csv(RAW_DATA_PATH)

        print("=" * 50)
        print(f"[EXTRACT] Loaded data shape: {df.shape}")
        print(f"[EXTRACT] Columns: {df.columns.tolist()}")
        print("=" * 50)

        return df

    except Exception as e:
        print(f"[EXTRACT ERROR] {e}")
        raise