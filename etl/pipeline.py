from etl.extract import extract_data
from etl.transform import transform_data
from etl.validate import validate_data
from etl.load import load_data

def run_pipeline():

    try:
        df = extract_data()
        df = transform_data(df)
        validate_data(df)
        load_data(df)

        print("[PIPELINE] ETL pipeline completed successfully")

    except Exception as e:
        print(f"[PIPELINE ERROR] {e}")
        raise


if __name__ == "__main__":
    run_pipeline()