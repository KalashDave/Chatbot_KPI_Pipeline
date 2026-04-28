"""
Script to create and update the SQLite tables
"""

import sqlite3
import pandas as pd
from pathlib import Path

# Define paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "chatbot_metrics.sqlite"
TABLE_NAME = "metrics"

def init_db():
    """Ensures the data directory exists."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_to_database(df: pd.DataFrame):
    """
    Validates data types and saves the pandas DataFrame to a SQLite database.
    Overwrites the existing table if it exists.
    """
    print(f"Connecting to database at {DB_PATH}...")
    init_db()
    
    # Validation/Formatting before inserting
    print("Validating data types...")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['csat_score'] = df['csat_score'].astype(int)
    df['average_handling_time'] = df['average_handling_time'].astype(float)
    
    # Validation for new boolean columns
    bool_cols = ['human_takeover', 'is_fallback', 'is_resolved', 'converted', 'would_be_ticket']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    
    with sqlite3.connect(DB_PATH) as conn:
        print(f"Writing {len(df)} rows to table '{TABLE_NAME}'...")
        # Write to SQLite
        df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
        print("Data successfully saved to database!")

def load_from_database() -> pd.DataFrame:
    """
    Loads the metrics table from the SQLite database.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Please run the pipeline first.")
        
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
        # Convert timestamp strings back to datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

if __name__ == "__main__":
    from ingest import ingest_data
    from process import process_data
    
    print("--- 1. Ingestion ---")
    raw_df = ingest_data()
    
    print("\n--- 2. Processing ---")
    processed_df = process_data(raw_df)
    
    print("\n--- 3. Database Storage ---")
    save_to_database(processed_df)
    
    # Test reading it back
    print("\n--- Testing Read ---")
    test_df = load_from_database()
    print(f"Successfully read {len(test_df)} rows from DB!")
