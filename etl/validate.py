def validate_data(df):

    try:
        assert df.isnull().sum().sum() == 0, "Missing values found"
        assert (df["Total_Amount"] >= 0).all(), "Negative sales found"
        assert (df["Quantity"] > 0).all(), "Invalid quantity found"

        print("[VALIDATE] Data validation passed")

    except Exception as e:
        print(f"[VALIDATE ERROR] {e}")
        raise