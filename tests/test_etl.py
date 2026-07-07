"""Unit tests for Shoplytics AI ETL transform and validation layers."""

import pandas as pd
import pytest

from etl.transform import transform_data, transform_single, _engineer_features, _normalise_columns
from etl.validate import validate_data, validate_single


def _sample_raw_row() -> dict:
    return {
        "Order_ID": "ORD-TEST-001",
        "Customer_ID": "CUST-99",
        "Date": "15-06-2025",
        "Age": 30,
        "Gender": "Male",
        "City": "Mumbai",
        "Product_Category": "Electronics",
        "Unit_Price": 1000.0,
        "Quantity": 2,
        "Discount_Amount": 100.0,
        "Total_Amount": 1900.0,
        "Payment_Method": "UPI",
        "Device_Type": "Mobile",
        "Session_Duration_Minutes": 10.0,
        "Pages_Viewed": 5.0,
        "Is_Returning_Customer": True,
        "Delivery_Time_Days": 3.0,
        "Customer_Rating": 4.0,
    }


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame([_sample_raw_row()])


from etl.dtypes import parse_bool


class TestParseBool:
    def test_true_variants(self):
        assert parse_bool("true") is True
        assert parse_bool("True") is True
        assert parse_bool("TRUE") is True
        assert parse_bool(1) is True
        assert parse_bool(True) is True

    def test_false_variants(self):
        assert parse_bool("false") is False
        assert parse_bool("0") is False
        assert parse_bool(0) is False
        assert parse_bool(False) is False


class TestTransform:
    def test_feature_engineering_profit(self):
        df = _sample_df()
        df = _normalise_columns(df)
        df = _engineer_features(df)

        assert df.loc[0, "Total_Sales"] == 1900.0
        assert df.loc[0, "Cost_Price"] == 700.0
        assert df.loc[0, "Profit"] == 1900.0 - (700.0 * 2)
        assert df.loc[0, "Engagement_Score"] == 50.0
        assert df.loc[0, "Is_Delayed"] == 0

    def test_discount_percentage(self):
        df = _sample_df()
        df = _normalise_columns(df)
        df = _engineer_features(df)

        expected = 100.0 / (1000.0 * 2)
        assert abs(df.loc[0, "Discount_Percentage"] - expected) < 1e-6

    def test_transform_single_returns_one_row(self):
        df = transform_single(_sample_raw_row())
        assert len(df) == 1
        assert "Profit" in df.columns
        assert "Engagement_Score" in df.columns

    def test_transform_data_drops_duplicates(self):
        df = pd.concat([_sample_df(), _sample_df()], ignore_index=True)
        result = transform_data(df)
        assert len(result) == 1


class TestValidate:
    def test_validate_data_passes_clean_df(self):
        df = transform_single(_sample_raw_row())
        assert validate_data(df) is True

    def test_validate_data_rejects_negative_quantity(self):
        row = _sample_raw_row()
        row["Quantity"] = 0
        df = transform_single(row)
        with pytest.raises(ValueError, match="Quantity"):
            validate_data(df)

    def test_validate_data_rejects_invalid_rating(self):
        row = _sample_raw_row()
        row["Customer_Rating"] = 6
        df = transform_single(row)
        with pytest.raises(ValueError, match="Rating"):
            validate_data(df)

    def test_validate_single_rejects_blank_order_id(self):
        row = _sample_raw_row()
        row["Order_ID"] = ""
        with pytest.raises(ValueError, match="Order_ID"):
            validate_single(row)

    def test_validate_single_passes_valid_record(self):
        validate_single(_sample_raw_row())
