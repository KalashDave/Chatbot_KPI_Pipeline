import pytest
import pandas as pd
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src import database

@pytest.fixture
def sample_processed_df():
    """Returns a dummy processed dataframe to insert into the db."""
    data = {
        'timestamp': pd.to_datetime(['2023-01-01 10:00:00', '2023-01-01 10:05:00']),
        'intent': ['check_balance', 'refund'],
        'average_handling_time': [150.5, 300.0],
        'csat_score': [4, 5],
        'is_fallback': [False, True],
        'human_takeover': [False, True],
        'is_resolved': [True, False],
        'would_be_ticket': [False, True],
        'converted': [True, False]
    }
    return pd.DataFrame(data)

def test_database_init(tmp_path, monkeypatch):
    """Test that init_db creates the data directory."""
    # Create a dummy path
    dummy_data_dir = tmp_path / "dummy_data"
    monkeypatch.setattr(database, "DATA_DIR", dummy_data_dir)
    
    # Ensure it doesn't exist yet
    assert not dummy_data_dir.exists()
    
    database.init_db()
    
    # Should be created
    assert dummy_data_dir.exists()

def test_save_and_load_database(sample_processed_df, tmp_path, monkeypatch):
    """Test saving to and loading from a sqlite database."""
    # Point DB_PATH to a temporary sqlite file
    dummy_db_path = tmp_path / "test_metrics.sqlite"
    monkeypatch.setattr(database, "DB_PATH", dummy_db_path)
    monkeypatch.setattr(database, "DATA_DIR", tmp_path)
    
    # Save the dataframe
    database.save_to_database(sample_processed_df)
    
    # Ensure the file was created
    assert dummy_db_path.exists()
    
    # Load the dataframe
    loaded_df = database.load_from_database()
    
    # Validate it matches what we inserted
    assert len(loaded_df) == 2
    assert pd.api.types.is_datetime64_any_dtype(loaded_df['timestamp'])
    # SQLite returns booleans as 0/1 integers
    assert loaded_df['is_fallback'].dtype in ['int64', 'int32', bool]
    assert loaded_df['csat_score'].dtype == 'int32' or loaded_df['csat_score'].dtype == 'int64'
    
    # Check values
    assert loaded_df.iloc[0]['intent'] == 'check_balance'
    assert loaded_df.iloc[1]['human_takeover'] == True

def test_load_database_missing(tmp_path, monkeypatch):
    """Test loading raises FileNotFoundError if DB doesn't exist."""
    missing_db_path = tmp_path / "does_not_exist.sqlite"
    monkeypatch.setattr(database, "DB_PATH", missing_db_path)
    
    with pytest.raises(FileNotFoundError, match="Database not found"):
        database.load_from_database()
