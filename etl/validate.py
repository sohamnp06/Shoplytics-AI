"""
validate.py
-----------
Business-rule validation for both batch and single-record ingestion.

Batch path:  validate_data(df)   → raises ValueError on any violation
Real-time:   validate_single(d)  → raises ValueError with a clear field-level message
"""


def validate_data(df):
    """Validate an entire DataFrame against all business rules.

    Raises ValueError immediately on the first violation so that
    invalid data never reaches PostgreSQL.
    """
    try:
        if df.isnull().sum().sum() > 0:
            raise ValueError("Missing values found in one or more columns.")

        if (df["Quantity"] <= 0).any():
            raise ValueError("Quantity must be greater than 0.")

        if (df["Total_Amount"] < 0).any():
            raise ValueError("Total Amount cannot be negative.")

        if (df["Unit_Price"] < 0).any():
            raise ValueError("Unit Price cannot be negative.")

        if (df["Customer_Rating"] < 0).any() or (df["Customer_Rating"] > 5).any():
            raise ValueError("Customer Rating must be between 0 and 5.")

        print("[VALIDATE] Batch validation passed.")
        return True

    except Exception as e:
        print(f"[VALIDATE ERROR] {e}")
        raise


def validate_single(data: dict):
    """Validate a single raw record (dict from the Flask form).

    Performs field-level checks before any transformation so the user
    gets a meaningful error message in the web UI.

    Args:
        data: Raw dict from request.form

    Raises:
        ValueError: with a human-readable message on the first failed rule.
    """
    errors = []

    # Required string identifiers
    for field in ("Order_ID", "Customer_ID", "Date", "City"):
        if not data.get(field, "").strip():
            errors.append(f"'{field}' is required and cannot be blank.")

    # Numeric range checks (values already cast to float by app.py)
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

    print("[VALIDATE] Single-record pre-validation passed.")