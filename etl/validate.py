"""
validate.py
-----------
Business-rule validation for both batch and single-record ingestion.

Batch path:  validate_data(df)              → raises ValueError on any violation
Real-time:   validate_single(d)             → field-level checks before transform
             validate_order_id_unique(id)   → prevents duplicate inserts in DB
"""

from sqlalchemy import text

from config import engine
from utils.logger import setup_logger

logger = setup_logger("etl.validate")


def validate_data(df):
    """Validate an entire DataFrame against all business rules."""
    try:
        if df.isnull().sum().sum() > 0:
            raise ValueError("Missing values found in one or more columns.")

        if df["Order_ID"].duplicated().any():
            raise ValueError("Duplicate Order_ID values found in batch data.")

        if (df["Quantity"] <= 0).any():
            raise ValueError("Quantity must be greater than 0.")

        if (df["Total_Amount"] < 0).any():
            raise ValueError("Total Amount cannot be negative.")

        if (df["Unit_Price"] < 0).any():
            raise ValueError("Unit Price cannot be negative.")

        if (df["Customer_Rating"] < 0).any() or (df["Customer_Rating"] > 5).any():
            raise ValueError("Customer Rating must be between 0 and 5.")

        logger.info("Batch validation passed.")
        return True

    except Exception as e:
        logger.error("Batch validation failed: %s", e)
        raise


def validate_single(data: dict):
    """Validate a single raw record (dict from the Flask form)."""
    errors = []

    for field in ("Order_ID", "Customer_ID", "Date", "City"):
        if not str(data.get(field, "")).strip():
            errors.append(f"'{field}' is required and cannot be blank.")

    try:
        qty = float(data.get("Quantity", 0))
        if qty <= 0:
            errors.append("Quantity must be greater than 0.")
    except (TypeError, ValueError):
        errors.append("Quantity must be a valid number.")

    try:
        unit_price = float(data.get("Unit_Price", 0))
        if unit_price < 0:
            errors.append("Unit Price cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Unit Price must be a valid number.")

    try:
        total = float(data.get("Total_Amount", 0))
        if total < 0:
            errors.append("Total Amount cannot be negative.")
    except (TypeError, ValueError):
        errors.append("Total Amount must be a valid number.")

    try:
        rating = float(data.get("Customer_Rating", 0))
        if not (0 <= rating <= 5):
            errors.append("Customer Rating must be between 0 and 5.")
    except (TypeError, ValueError):
        errors.append("Customer Rating must be a valid number.")

    if errors:
        raise ValueError(" | ".join(errors))

    logger.info("Single-record pre-validation passed.")


def validate_order_id_unique(order_id: str) -> None:
    """Ensure Order_ID does not already exist in PostgreSQL."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text('SELECT 1 FROM sales_data WHERE "Order_ID" = :oid LIMIT 1'),
                {"oid": order_id},
            )
            if result.fetchone():
                raise ValueError(
                    f"Order ID '{order_id}' already exists. Use a unique Order ID."
                )
        logger.info("Order_ID '%s' is unique.", order_id)

    except ValueError:
        raise
    except Exception as e:
        err = str(e).lower()
        if "does not exist" in err or "undefinedtable" in err:
            logger.info("sales_data table not found — skipping duplicate check.")
            return
        logger.error("Duplicate check failed: %s", e)
        raise
