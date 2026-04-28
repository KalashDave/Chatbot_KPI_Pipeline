import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to path so we can import process
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.process import process_data

@pytest.fixture
def sample_df():
    data = {
        'intent': ['contact_customer_service', 'check_balance', 'refund_request'],
        'response': ['I am transferring you to an agent.', 'Your balance is 100.', 'I will process your refund.'],
    }
    return pd.DataFrame(data)

def test_csat_bounds(sample_df):
    processed = process_data(sample_df)
    assert processed['csat_score'].min() >= 1
    assert processed['csat_score'].max() <= 5

def test_new_kpi_columns_exist(sample_df):
    processed = process_data(sample_df)
    bool_cols = ['is_fallback', 'human_takeover', 'is_resolved', 'converted', 'would_be_ticket']
    for col in bool_cols:
        assert col in processed.columns
        assert processed[col].dtype == bool

def test_average_handling_time_type(sample_df):
    processed = process_data(sample_df)
    assert processed['average_handling_time'].dtype in [np.float64, float, int, np.int64]
