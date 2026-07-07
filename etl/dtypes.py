"""
dtypes.py
---------
PostgreSQL column types and DataFrame coercion helpers.

Ensures every row loaded into sales_data uses types that match Power BI
(BOOLEAN, numeric, DATE) instead of plain text strings.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import Boolean, Date, Float, Integer, Text

# Full SQLAlchemy dtype map used when creating/replacing the table.
PG_DTYPES = {
    "Order_ID": Text(),
    "Customer_ID": Text(),
    "Date": Date(),
    "Age": Float(),
    "Gender": Text(),
    "City": Text(),
    "Product_Category": Text(),
    "Unit_Price": Float(),
    "Quantity": Float(),
    "Discount_Amount": Float(),
    "Total_Amount": Float(),
    "Payment_Method": Text(),
    "Device_Type": Text(),
    "Session_Duration_Minutes": Float(),
    "Pages_Viewed": Float(),
    "Is_Returning_Customer": Boolean(),
    "Delivery_Time_Days": Float(),
    "Customer_Rating": Float(),
    "Total_Sales": Float(),
    "Avg_Item_Price": Float(),
    "Discount_Percentage": Float(),
    "Cost_Price": Float(),
    "Profit": Float(),
    "Profit_Margin": Float(),
    "Engagement_Score": Float(),
    "Pages_Per_Minute": Float(),
    "Is_Delayed": Integer(),
}

_NUMERIC_COLUMNS = [
    "Age", "Unit_Price", "Quantity", "Discount_Amount", "Total_Amount",
    "Session_Duration_Minutes", "Pages_Viewed", "Delivery_Time_Days",
    "Customer_Rating", "Total_Sales", "Avg_Item_Price", "Discount_Percentage",
    "Cost_Price", "Profit", "Profit_Margin", "Engagement_Score",
    "Pages_Per_Minute",
]

_TRUTHY = {"true", "t", "1", "yes", "y"}
_FALSY = {"false", "f", "0", "no", "n", ""}


def parse_bool(value) -> bool:
    """Convert mixed text/bool/numeric values to a proper Python bool."""
    if isinstance(value, bool):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    if isinstance(value, (int, float)):
        return bool(value)

    text = str(value).strip().lower()
    if text in _TRUTHY:
        return True
    if text in _FALSY:
        return False
    return text == "true"


def normalize_date_series(series: pd.Series) -> pd.Series:
    """Parse dates and strip time — store date-only (YYYY-MM-DD)."""
    parsed = pd.to_datetime(series, dayfirst=True, errors="coerce")
    return parsed.dt.normalize()


def coerce_dataframe_for_pg(df: pd.DataFrame) -> pd.DataFrame:
    """Cast DataFrame columns to PostgreSQL-compatible dtypes before load."""
    out = df.copy()

    if "Date" in out.columns:
        out["Date"] = normalize_date_series(out["Date"])

    for col in _NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    if "Is_Returning_Customer" in out.columns:
        out["Is_Returning_Customer"] = out["Is_Returning_Customer"].map(parse_bool)

    if "Is_Delayed" in out.columns:
        out["Is_Delayed"] = (
            pd.to_numeric(out["Is_Delayed"], errors="coerce")
            .fillna(0)
            .astype("int64")
        )

    return out
