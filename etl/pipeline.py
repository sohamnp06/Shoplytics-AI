"""
pipeline.py
-----------
Orchestrates the full batch ETL pipeline:

  extract → transform → validate → load (replace)

Batch reload reads the raw source file (CSV or Excel), which includes
records appended by the Flask form, keeping PostgreSQL in sync.
"""

from etl.extract import extract_data
from etl.transform import transform_data
from etl.validate import validate_data
from etl.load import load_data
from etl.migrate_schema import migrate_schema
from utils.logger import setup_logger

logger = setup_logger("etl.pipeline")


def run_pipeline():
    try:
        logger.info("Starting batch ETL pipeline.")

        migrate_schema()

        df = extract_data()
        df = transform_data(df)
        validate_data(df)
        load_data(df, mode="replace")

        logger.info("Batch ETL pipeline completed successfully.")

    except Exception as e:
        logger.error("Pipeline failed: %s", e)
        raise


if __name__ == "__main__":
    run_pipeline()
