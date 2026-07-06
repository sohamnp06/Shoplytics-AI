-- =============================================================
-- Shoplytics AI — PostgreSQL DDL
-- Table: sales_data
-- 
-- This schema is auto-applied by SQLAlchemy (via pandas.to_sql).
-- This file exists for documentation and manual reproducibility.
--
-- To recreate the table manually:
--   psql -U postgres -d sales_db -f database/schema.sql
-- =============================================================

DROP TABLE IF EXISTS sales_data;

CREATE TABLE sales_data (
    -- ── Identifiers ───────────────────────────────────────────
    "Order_ID"                  TEXT,
    "Customer_ID"               TEXT,
    "Date"                      TIMESTAMP,

    -- ── Customer Demographics ──────────────────────────────────
    "Age"                       DOUBLE PRECISION,
    "Gender"                    TEXT,
    "City"                      TEXT,

    -- ── Product & Transaction ──────────────────────────────────
    "Product_Category"          TEXT,
    "Unit_Price"                DOUBLE PRECISION,
    "Quantity"                  DOUBLE PRECISION,
    "Discount_Amount"           DOUBLE PRECISION,
    "Total_Amount"              DOUBLE PRECISION,
    "Payment_Method"            TEXT,

    -- ── Session Behaviour ─────────────────────────────────────
    "Device_Type"               TEXT,
    "Session_Duration_Minutes"  DOUBLE PRECISION,
    "Pages_Viewed"              DOUBLE PRECISION,
    "Is_Returning_Customer"     BOOLEAN,

    -- ── Delivery ──────────────────────────────────────────────
    "Delivery_Time_Days"        DOUBLE PRECISION,
    "Customer_Rating"           DOUBLE PRECISION,

    -- ── Engineered Features ───────────────────────────────────
    "Total_Sales"               DOUBLE PRECISION,   -- alias for Total_Amount
    "Avg_Item_Price"            DOUBLE PRECISION,   -- Total_Amount / Quantity
    "Discount_Percentage"       DOUBLE PRECISION,   -- Discount_Amount / (Unit_Price * Quantity)
    "Cost_Price"                DOUBLE PRECISION,   -- Unit_Price * 0.70
    "Profit"                    DOUBLE PRECISION,   -- Total_Amount - (Cost_Price * Quantity)
    "Profit_Margin"             DOUBLE PRECISION,   -- Profit / Total_Amount
    "Engagement_Score"          DOUBLE PRECISION,   -- Session_Duration_Minutes * Pages_Viewed
    "Pages_Per_Minute"          DOUBLE PRECISION,   -- Pages_Viewed / Session_Duration_Minutes
    "Is_Delayed"                INTEGER             -- 1 if Delivery_Time_Days > 7, else 0
);

-- Index for common filter operations in Power BI
CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales_data ("Date");
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_data ("Product_Category");
CREATE INDEX IF NOT EXISTS idx_sales_city     ON sales_data ("City");
