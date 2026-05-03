import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mock sqlite and pandas before importing streamlit_app to prevent it from reading the real DB
dummy_df = pd.DataFrame({
    'timestamp': pd.to_datetime(['2023-01-01', '2023-01-02']),
    'intent': ['check_balance', 'refund'],
    'average_handling_time': [150.5, 300.0],
    'csat_score': [4, 5],
    'is_fallback': [False, True],
    'human_takeover': [False, True],
    'is_resolved': [True, False],
    'would_be_ticket': [False, True],
    'converted': [True, False],
    'user_id': ['U1', 'U2']
})

with patch('pandas.read_sql', return_value=dummy_df), \
     patch('sqlite3.connect', MagicMock()), \
     patch('streamlit.stop'): # Prevent st.stop() from raising StopException if data is empty
    from src import streamlit_app

def test_streamlit_app_import():
    """Verify that the Streamlit app script executes top-to-bottom without throwing syntax or logic errors."""
    assert streamlit_app.DB_PATH is not None

def test_make_metric_card():
    """Verify the helper function generates the correct raw HTML."""
    html_output = streamlit_app.make_metric_card(
        title="Test Metric", 
        value="99%", 
        description="A test description", 
        benchmark="> 50%", 
        icon="⭐", 
        bar_color="#FFFFFF", 
        progress_pct=50
    )
    
    # Check that our inputs were correctly injected into the HTML string
    assert "Test Metric" in html_output
    assert "99%" in html_output
    assert "A test description" in html_output
    assert "width: 50%" in html_output # Tests the clamping and percentage injection
    
def test_make_metric_card_bounds():
    """Verify that progress_pct is clamped between 0 and 100."""
    html_output = streamlit_app.make_metric_card("T", "V", "D", "B", "I", "C", 150)
    assert "width: 100%" in html_output
    
    html_output_low = streamlit_app.make_metric_card("T", "V", "D", "B", "I", "C", -50)
    assert "width: 0%" in html_output_low
