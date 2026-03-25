import pandas as pd
import numpy as np

def apply_transformations(df):

    df.columns = df.columns.str.strip()
    df.columns = df.columns.str.replace(" ", "_")
    df.columns = df.columns.str.replace(r"[^\w_]", "", regex=True)

    df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)

    df["Total_Sales"] = df["Total_Amount"]

    df["Avg_Item_Price"] = df["Total_Amount"] / df["Quantity"]

    df["Discount_Percentage"] = np.where(
        df["Unit_Price"] * df["Quantity"] == 0,
        0,
        df["Discount_Amount"] / (df["Unit_Price"] * df["Quantity"])
    )

    df["Cost_Price"] = df["Unit_Price"] * 0.7
    df["Profit"] = df["Total_Amount"] - df["Cost_Price"]
    df["Profit_Margin"] = df["Profit"] / df["Total_Amount"]

    df["Engagement_Score"] = df["Session_Duration_Minutes"] * df["Pages_Viewed"]

    df["Pages_Per_Minute"] = np.where(
        df["Session_Duration_Minutes"] == 0,
        0,
        df["Pages_Viewed"] / df["Session_Duration_Minutes"]
    )

    df["Is_Delayed"] = (df["Delivery_Time_Days"] > 7).astype(int)

    final_columns = [
        "Order_ID", "Customer_ID", "Date", "Age", "Gender", "City",
        "Product_Category", "Unit_Price", "Quantity", "Discount_Amount",
        "Total_Amount", "Payment_Method", "Device_Type",
        "Session_Duration_Minutes", "Pages_Viewed",
        "Is_Returning_Customer", "Delivery_Time_Days",
        "Customer_Rating", "Total_Sales", "Avg_Item_Price",
        "Discount_Percentage", "Cost_Price", "Profit",
        "Profit_Margin", "Engagement_Score",
        "Pages_Per_Minute", "Is_Delayed"
    ]

    df = df[final_columns]

    return df

def transform_data(df):

    try:
      
        df.drop_duplicates(inplace=True)
        df.dropna(inplace=True)

        df = apply_transformations(df)

        print(f"[TRANSFORM] Batch Completed: {df.shape}")

        return df

    except Exception as e:
        print(f"[TRANSFORM ERROR - BATCH] {e}")
        raise

def transform_single(data: dict):

    try:
        df = pd.DataFrame([data])

        df = apply_transformations(df)

        print("[TRANSFORM] Single record processed")

        return df

    except Exception as e:
        print(f"[TRANSFORM ERROR - SINGLE] {e}")
        raise