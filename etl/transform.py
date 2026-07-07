"""
transform.py
------------
Transformation logic for both batch and real-time (single-record) ingestion.

Batch path:  transform_data(df)      → cleans, deduplicates, engineers features
Real-time:   transform_single(data)  → builds a 1-row DataFrame and engineers features
"""

import pandas as pd
import numpy as np

from utils.logger import setup_logger

logger = setup_logger("etl.transform")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and normalise column names to snake_case-safe identifiers."""
    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(" ", "_", regex=False)
    df.columns = df.columns.str.replace(r"[^\w_]", "", regex=True)
    return df


def _normalise_raw_types(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce raw CSV/Excel string columns to proper types before feature engineering."""
    from etl.dtypes import parse_bool

    if "Is_Returning_Customer" in df.columns:
        df["Is_Returning_Customer"] = df["Is_Returning_Customer"].map(parse_bool)

    numeric_cols = [
        "Age", "Unit_Price", "Quantity", "Discount_Amount", "Total_Amount",
        "Session_Duration_Minutes", "Pages_Viewed", "Delivery_Time_Days",
        "Customer_Rating",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all feature engineering steps in-place and return the DataFrame."""

    # Parse date — dayfirst handles DD-MM-YYYY; keep date-only (no time)
    from etl.dtypes import normalize_date_series
    df["Date"] = normalize_date_series(df["Date"])

    # ----- Financial features -----
    df["Total_Sales"] = df["Total_Amount"]

    # Guard against zero quantity to avoid division errors
    df["Avg_Item_Price"] = np.where(
        df["Quantity"] == 0,
        0,
        df["Total_Amount"] / df["Quantity"]
    )

    df["Discount_Percentage"] = np.where(
        df["Unit_Price"] * df["Quantity"] == 0,
        0,
        df["Discount_Amount"] / (df["Unit_Price"] * df["Quantity"])
    )

    # Assume cost is 70 % of unit price (simplified COGS model)
    df["Cost_Price"] = df["Unit_Price"] * 0.7
    df["Profit"] = df["Total_Amount"] - (df["Cost_Price"] * df["Quantity"])

    # Guard against zero Total_Amount for margin calculation
    df["Profit_Margin"] = np.where(
        df["Total_Amount"] == 0,
        0,
        df["Profit"] / df["Total_Amount"]
    )

    # ----- Engagement features -----
    df["Engagement_Score"] = df["Session_Duration_Minutes"] * df["Pages_Viewed"]

    df["Pages_Per_Minute"] = np.where(
        df["Session_Duration_Minutes"] == 0,
        0,
        df["Pages_Viewed"] / df["Session_Duration_Minutes"]
    )

    # ----- Delivery feature -----
    # Cast explicitly to int64 so SQLAlchemy maps this to INTEGER (not BOOLEAN)
    # on single-row DataFrames where dtype inference can go wrong.
    df["Is_Delayed"] = (df["Delivery_Time_Days"] > 7).astype("int64")

    return df


# Canonical column order — matches PostgreSQL table schema
_FINAL_COLUMNS = [
    "Order_ID", "Customer_ID", "Date", "Age", "Gender", "City",
    "Product_Category", "Unit_Price", "Quantity", "Discount_Amount",
    "Total_Amount", "Payment_Method", "Device_Type",
    "Session_Duration_Minutes", "Pages_Viewed",
    "Is_Returning_Customer", "Delivery_Time_Days",
    "Customer_Rating", "Total_Sales", "Avg_Item_Price",
    "Discount_Percentage", "Cost_Price", "Profit",
    "Profit_Margin", "Engagement_Score",
    "Pages_Per_Minute", "Is_Delayed",
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Batch transformation: deduplicate, drop nulls, normalise columns,
    engineer features, and enforce canonical column order.

    Args:
        df: Raw DataFrame from extract step.

    Returns:
        Cleaned and feature-enriched DataFrame.
    """
    try:
        df = df.drop_duplicates()
        df = df.dropna()

        df = _normalise_columns(df)
        df = _normalise_raw_types(df)
        df = _engineer_features(df)

        df = df[_FINAL_COLUMNS]

        logger.info("Batch completed — shape: %s", df.shape)
        return df

    except Exception as e:
        logger.error("Batch transform failed: %s", e)
        raise


def transform_single(data: dict) -> pd.DataFrame:
    """Real-time transformation for a single record coming from the Flask form.

    The dict keys are already in the correct format (the form uses the exact
    field names), so column normalisation is skipped. Feature engineering
    is applied identically to the batch path.

    Args:
        data: Validated dict from request.form (numeric fields already cast).

    Returns:
        1-row DataFrame with all engineered features, ready for PostgreSQL.
    """
    try:
        df = pd.DataFrame([data])
        df = _normalise_raw_types(df)
        df = _engineer_features(df)

        # Select only the columns that exist in the final schema
        available = [c for c in _FINAL_COLUMNS if c in df.columns]
        df = df[available]

        logger.info("Single-record transformation completed.")
        return df

    except Exception as e:
        logger.error("Single transform failed: %s", e)
        raise