from etl.extract import extract_data
from etl.transform import transform_data
from etl.validate import validate_data
from etl.load import load_data

def run_pipeline():

    try:
        print("\n🚀 Starting ETL Pipeline...\n")

        # -------------------------
        # EXTRACT
        # -------------------------
        df = extract_data()

        # -------------------------
        # TRANSFORM
        # -------------------------
        df = transform_data(df)

        # -------------------------
        # VALIDATE
        # -------------------------
        validate_data(df)

        # -------------------------
        # LOAD (BATCH → REPLACE)
        # -------------------------
        load_data(df, mode="replace")

        print("\n✅ ETL pipeline completed successfully\n")

    except Exception as e:
        print(f"\n❌ PIPELINE ERROR: {e}\n")
        raise


if __name__ == "__main__":
    run_pipeline()