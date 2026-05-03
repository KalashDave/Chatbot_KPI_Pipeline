import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.ingest import ingest_data

@patch("src.ingest.load_dotenv")
def test_ingest_data_missing_token(mock_load_dotenv, monkeypatch):
    """
    Test that ingest_data raises a ValueError if HF_TOKEN is not in the environment.
    """
    # Force HF_TOKEN to be missing
    monkeypatch.delenv("HF_TOKEN", raising=False)
    
    with pytest.raises(ValueError, match="HF_TOKEN not found in environment variables"):
        ingest_data()

@patch("src.ingest.load_dataset")
@patch("src.ingest.login")
def test_ingest_data_success(mock_login, mock_load_dataset, monkeypatch):
    """
    Test that ingest_data correctly loads from HF and returns a DataFrame
    without making real network requests.
    """
    # Provide a fake token
    monkeypatch.setenv("HF_TOKEN", "fake_token_123")
    
    # Create a mock HF dataset
    mock_dataset = MagicMock()
    # The to_pandas method should return a dummy DataFrame
    dummy_df = pd.DataFrame({"intent": ["test"], "response": ["test"]})
    mock_dataset.to_pandas.return_value = dummy_df
    # When load_dataset is called, return our mock dataset
    mock_load_dataset.return_value = mock_dataset
    
    # Call the function
    df = ingest_data()
    
    # Assertions
    mock_login.assert_called_once_with(token="fake_token_123")
    mock_load_dataset.assert_called_once_with("bitext/Bitext-customer-support-llm-chatbot-training-dataset", split="train")
    
    # Ensure it returns the dataframe
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert list(df.columns) == ["intent", "response"]
