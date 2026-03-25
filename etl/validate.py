def validate_data(df):

    try:
        # -------------------------
        # NULL CHECK
        # -------------------------
        if df.isnull().sum().sum() > 0:
            raise ValueError("❌ Missing values found")

        # -------------------------
        # BUSINESS RULES
        # -------------------------
        if (df["Quantity"] <= 0).any():
            raise ValueError("❌ Invalid quantity (<= 0)")

        if (df["Total_Amount"] < 0).any():
            raise ValueError("❌ Negative Total Amount")

        if (df["Unit_Price"] < 0).any():
            raise ValueError("❌ Negative Unit Price")

        if (df["Customer_Rating"] < 0).any() or (df["Customer_Rating"] > 5).any():
            raise ValueError("❌ Invalid rating (must be 0–5)")

        print("[VALIDATE] Data validation passed")

        return True

    except Exception as e:
        print(f"[VALIDATE ERROR] {e}")
        raise