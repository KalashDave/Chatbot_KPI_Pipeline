"""
Script to create and update the SQLite tables
"""

import sqlite3
import pandas as pd
from pathlib import Path

# --- Configuration & Paths ---
# Resolve the absolute path of the root directory (two levels up from this script)
BASE_DIR = Path(__file__).resolve().parent.parent
# Define the directory where the SQLite database file will live
DATA_DIR = BASE_DIR / "data"
# Define the absolute path to the actual .sqlite database file
DB_PATH = DATA_DIR / "chatbot_metrics.sqlite"
# Define the name of the table that will hold our operational telemetry
TABLE_NAME = "metrics"

def init_db():
    """
    Ensures the data directory exists before we attempt to write a database file into it.
    If the directory already exists, it does nothing (exist_ok=True).
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_to_database(df: pd.DataFrame):
    """
    Validates data types and saves the pandas DataFrame to a SQLite database.
    Overwrites the existing table if it exists.
    
    This function acts as the final step of the ETL (Extract, Transform, Load) pipeline,
    pushing our processed pandas dataframe into a persistent, queryable relational database.
    """
    print(f"Connecting to database at {DB_PATH}...")
    
    # Ensure the parent directory for the database exists
    init_db()
    
    # --- Validation & Formatting ---
    print("Validating data types...")
    
    # Enforce strict data types to prevent SQLite insertion errors
    # Timestamps must be proper datetime objects so they can be queried by date ranges
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # CSAT scores are distinct integers (1 to 5 stars)
    df['csat_score'] = df['csat_score'].astype(int)
    
    # Average Handling Time is stored as a float since it can have decimal seconds
    df['average_handling_time'] = df['average_handling_time'].astype(float)
    
    # Ensure all our synthetic KPI markers are strictly boolean (True/False)
    bool_cols = ['human_takeover', 'is_fallback', 'is_resolved', 'converted', 'would_be_ticket']
    for col in bool_cols:
        # We check if the column exists to prevent KeyError if the dataframe is missing columns
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    # --- Database Insertion ---
    # Open a context manager for the SQLite connection. This ensures the connection
    # is safely and automatically closed when the block ends, even if an error occurs.
    with sqlite3.connect(DB_PATH) as conn:
        print(f"Writing {len(df)} rows to table '{TABLE_NAME}'...")
        
        # Use pandas built-in to_sql method to write the dataframe directly to SQLite.
        # if_exists='replace' ensures that running the pipeline multiple times simply
        # overwrites the old dummy data rather than infinitely appending to it.
        # index=False prevents pandas from writing its arbitrary row numbers to the database.
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
        
        print("Data successfully saved to database!")

def load_from_database() -> pd.DataFrame:
    """
    Loads the metrics table from the SQLite database back into a pandas DataFrame.
    This is the function called by the Dash and Streamlit frontends to fetch live data.
    """
    # Defensive programming: ensure the database file actually exists before trying to query it
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run the pipeline first.")
        
    # Open a read connection to the database
    with sqlite3.connect(DB_PATH) as conn:
        # Execute a raw SQL query to pull all rows and columns from the metrics table
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
        
        # When SQLite returns datetime data, it comes back as strings.
        # We must cast it back to proper pandas datetime objects so the dashboards
        # can correctly filter by date ranges.
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df

if __name__ == "__main__":
    # Local integration test block. 
    # If you run `python src/database.py` directly, it will execute the entire ETL pipeline
    # from start to finish to ensure data flows correctly from Hugging Face into the local DB.
    from ingest import ingest_data
    from process import process_data
    
    print("--- 1. Ingestion ---")
    raw_df = ingest_data()
    
    print("\n--- 2. Processing ---")
    processed_df = process_data(raw_df)
    
    print("\n--- 3. Database Storage ---")
    save_to_database(processed_df)
    
    # Test reading it back to confirm the write was successful
    print("\n--- Testing Read ---")
    test_df = load_from_database()
    print(f"Successfully read {len(test_df)} rows from DB!")
