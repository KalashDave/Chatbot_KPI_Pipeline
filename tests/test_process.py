"""
Unit tests for the data processing module.
These tests verify that our synthetic KPI generation logic produces valid, bounded outputs.
"""

import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add the project root directory to the Python system path.
# This allows us to import modules from the 'src' directory (e.g., src.process)
# without throwing ModuleNotFoundError during pytest execution.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.process import process_data

@pytest.fixture
def sample_df():
    """
    Pytest fixture that provides a minimal, mock pandas DataFrame representing
    raw ingested chat data. This is injected into the test functions below to 
    isolate the tests from the actual Hugging Face API or local database.
    """
    data = {
        'intent': ['contact_customer_service'] * 1000,
        'response': ['I am transferring you to an agent.'] * 1000,
    }
    return pd.DataFrame(data)

def test_csat_bounds(sample_df):
    """
    Verifies that the engineered Customer Satisfaction (CSAT) score
    remains strictly within the realistic 1 to 5 star rating bounds.
    """
    processed = process_data(sample_df)
    assert processed['csat_score'].min() >= 1
    assert processed['csat_score'].max() <= 5

def test_new_kpi_columns_exist(sample_df):
    """
    Ensures that the process_data function actually generates all the necessary
    synthetic boolean operational columns required by the dashboard.
    """
    processed = process_data(sample_df)
    bool_cols = ['is_fallback', 'human_takeover', 'is_resolved', 'converted', 'would_be_ticket']
    for col in bool_cols:
        assert col in processed.columns
        assert processed[col].dtype == bool

def test_average_handling_time_type(sample_df):
    """
    Verifies that the generated Average Handling Time (AHT) is numeric and within bounds.
    """
    processed = process_data(sample_df)
    assert processed['average_handling_time'].dtype in [np.float64, float, int, np.int64]
    # Bound checks from the code (120 to 1500)
    assert processed['average_handling_time'].min() >= 120
    assert processed['average_handling_time'].max() <= 1500

def test_reproducibility(sample_df):
    """
    Verify that because we set np.random.seed(42), the function 
    generates the exact same data multiple times.
    """
    processed_1 = process_data(sample_df)
    processed_2 = process_data(sample_df)
    pd.testing.assert_frame_equal(processed_1, processed_2)

def test_probabilities(sample_df):
    """
    Verify that the synthetic probabilities loosely match the benchmarks.
    """
    processed = process_data(sample_df)
    
    fallback_rate = processed['is_fallback'].mean()
    # Expect ~6% fallbacks
    assert 0.02 <= fallback_rate <= 0.10
    
    conversion_rate = processed['converted'].mean()
    # Expect ~10% conversion
    assert 0.05 <= conversion_rate <= 0.15
    
    # Check return users (~65% unique users means some return rate)
    unique_users = processed['user_id'].nunique()
    assert unique_users <= len(processed) * 0.70
