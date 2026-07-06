"""
app.py
------
Flask application for Shoplytics AI.

Routes
------
GET  /              → Sales data entry form
POST /submit        → Real-time single-record ETL (transform → validate → append)
POST /run-etl       → Trigger batch ETL pipeline on-demand (admin action)
GET  /api/recent    → JSON — last N rows from sales_data (for live table in UI)
GET  /api/stats     → JSON — KPI summary (total rows, revenue, avg rating)
"""

from flask import Flask, request, render_template, jsonify
import pandas as pd
from sqlalchemy import text

from config import DB_URL
from etl.transform import transform_single
from etl.validate import validate_data, validate_single
from etl.load import load_data, append_raw_csv, engine
from etl.pipeline import run_pipeline

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cast_form_numerics(data: dict) -> dict:
    """Cast numeric form fields from strings to float, defaulting blanks to 0."""
    numeric_fields = [
        "Age", "Unit_Price", "Quantity", "Discount_Amount",
        "Total_Amount", "Session_Duration_Minutes",
        "Pages_Viewed", "Delivery_Time_Days", "Customer_Rating",
    ]
    for field in numeric_fields:
        raw = data.get(field, "")
        data[field] = float(raw) if str(raw).strip() != "" else 0.0
    return data


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# Real-time single-record ingestion
# ---------------------------------------------------------------------------

@app.route("/submit", methods=["POST"])
def submit():
    """Accept a single order record from the web form, run it through the
    transform → validate → append pipeline, and return the rendered page
    with a success or error message.
    """
    try:
        data = request.form.to_dict()

        # Cast numeric fields
        data = _cast_form_numerics(data)

        # Boolean flag
        data["Is_Returning_Customer"] = (
            True if data.get("Is_Returning_Customer") == "1" else False
        )

        # Pre-validation (field-level, before transformation)
        validate_single(data)

        # ── Step 1: Append raw record to SalesData.csv (pre-transformation) ──
        # Keep a raw copy so we save the original date string and input values.
        append_raw_csv(data)

        # ── Step 2: Transform single record (feature engineering) ────────────
        df = transform_single(data)

        # ── Step 3: Post-transform validation (DataFrame-level rules) ─────────
        validate_data(df)

        # ── Step 4: Append to PostgreSQL + CleanedSalesData.csv ──────────────
        load_data(df, mode="append")

        return render_template(
            "index.html",
            message=(
                "✅ Data inserted successfully! "
                "Record appended to SalesData.csv, CleanedSalesData.csv, and PostgreSQL. "
                "Refresh Power BI to see the update."
            ),
        )

    except Exception as e:
        return render_template("index.html", message=f"❌ Error: {str(e)}")


# ---------------------------------------------------------------------------
# Batch ETL trigger (admin / on-demand)
# ---------------------------------------------------------------------------

@app.route("/run-etl", methods=["POST"])
def run_etl():
    """Trigger the full batch ETL pipeline (extract → transform → validate → replace).

    WARNING: This replaces the entire sales_data table.
    Use only when you want to reload data from the raw CSV.
    """
    try:
        run_pipeline()
        return jsonify({"status": "success", "message": "Batch ETL pipeline completed."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# JSON API — live data for the UI
# ---------------------------------------------------------------------------

@app.route("/api/recent")
def api_recent():
    """Return the most recent N rows from sales_data as JSON.

    Query param: ?limit=N  (default 10, max 50)
    """
    try:
        limit = min(int(request.args.get("limit", 10)), 50)
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    'SELECT "Order_ID", "Customer_ID", "Date", "City", '
                    '"Product_Category", "Total_Amount", "Profit", '
                    '"Customer_Rating", "Is_Delayed" '
                    'FROM sales_data '
                    'ORDER BY "Date" DESC '
                    'LIMIT :lim'
                ),
                {"lim": limit},
            )
            rows = [dict(row._mapping) for row in result]

        # Serialise dates to ISO strings
        for row in rows:
            if row.get("Date") is not None:
                row["Date"] = str(row["Date"])[:10]

        return jsonify({"status": "ok", "count": len(rows), "data": rows})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """Return high-level KPI metrics from sales_data as JSON."""
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    'SELECT '
                    'COUNT(*) AS total_records, '
                    'ROUND(SUM("Total_Amount")::numeric, 2) AS total_revenue, '
                    'ROUND(AVG("Customer_Rating")::numeric, 2) AS avg_rating, '
                    'ROUND(SUM("Profit")::numeric, 2) AS total_profit '
                    'FROM sales_data'
                )
            )
            row = result.fetchone()
            stats = dict(row._mapping) if row else {}

        # jsonify can't serialise Decimal — convert to float
        stats = {k: float(v) if v is not None else 0 for k, v in stats.items()}
        return jsonify({"status": "ok", "data": stats})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)