"""
config.py
---------
Central configuration for Shoplytics AI.

Loads environment variables from .env and exposes:
  - DB_CONFIG / DB_URL  → PostgreSQL connection string
  - engine              → shared SQLAlchemy engine (import everywhere)
  - RAW_DATA_PATH       → batch input  (Excel or CSV)
  - CLEANED_DATA_PATH   → curated output CSV
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

load_dotenv()

DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "database": os.getenv("DB_NAME"),
}

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Default paths fall back to existing project files when .env omits them.
RAW_DATA_PATH = os.getenv("RAW_DATA_PATH") or str(DATA_DIR / "SalesData.csv")
CLEANED_DATA_PATH = os.getenv("CLEANED_DATA_PATH") or str(DATA_DIR / "CleanedSalesData.csv")

# Single shared engine — import this in load.py, app.py, seed_from_cleaned.py, etc.
engine = create_engine(DB_URL, pool_pre_ping=True)
