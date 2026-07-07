-- =============================================================
-- Shoplytics AI — PostgreSQL DDL
-- Table: sales_data
--
-- Auto-created by pandas.to_sql on first load.
-- This file is for documentation and manual reproducibility.
--
-- Apply manually:
--   psql -U <user> -d <dbname> -f database/schema.sql
-- =============================================================

DROP TABLE IF EXISTS sales_data;

CREATE TABLE sales_data (
    -- ── Identifiers ───────────────────────────────────────────
    "Order_ID"                  TEXT        NOT NULL,
    "Customer_ID"               TEXT        NOT NULL,
    "Date"                      DATE        NOT NULL,

    -- ── Customer Demographics ──────────────────────────────────
    "Age"                       DOUBLE PRECISION,
    "Gender"                    TEXT,
    "City"                      TEXT        NOT NULL,

    -- ── Product & Transaction ──────────────────────────────────
    "Product_Category"          TEXT,
    "Unit_Price"                DOUBLE PRECISION  NOT NULL,
    "Quantity"                  DOUBLE PRECISION  NOT NULL,
    "Discount_Amount"           DOUBLE PRECISION,
    "Total_Amount"              DOUBLE PRECISION  NOT NULL,
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
    "Total_Sales"               DOUBLE PRECISION,
    "Avg_Item_Price"            DOUBLE PRECISION,
    "Discount_Percentage"       DOUBLE PRECISION,
    "Cost_Price"                DOUBLE PRECISION,
    "Profit"                    DOUBLE PRECISION,
    "Profit_Margin"             DOUBLE PRECISION,
    "Engagement_Score"          DOUBLE PRECISION,
    "Pages_Per_Minute"          DOUBLE PRECISION,
    "Is_Delayed"                INTEGER,

    -- ── Constraints ───────────────────────────────────────────
    CONSTRAINT pk_sales_order_id PRIMARY KEY ("Order_ID"),
    CONSTRAINT chk_quantity_positive CHECK ("Quantity" > 0),
    CONSTRAINT chk_unit_price_non_negative CHECK ("Unit_Price" >= 0),
    CONSTRAINT chk_total_amount_non_negative CHECK ("Total_Amount" >= 0),
    CONSTRAINT chk_rating_range CHECK ("Customer_Rating" >= 0 AND "Customer_Rating" <= 5)
);

CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales_data ("Date");
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales_data ("Product_Category");
CREATE INDEX IF NOT EXISTS idx_sales_city     ON sales_data ("City");
