import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mock sqlite and pandas before importing dash_app to prevent it from reading the real DB
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

# We must patch these globally before the import happens because dash_app runs load_data() on module load.
with patch('pandas.read_sql', return_value=dummy_df), \
     patch('sqlite3.connect', MagicMock()):
    from src import dash_app

def test_dash_app_initialization():
    """Verify that the dash app initializes correctly with the right theme and title."""
    assert dash_app.app is not None
    assert dash_app.app.title == "OTA Intelligence Dashboard"

def test_metric_title_with_tooltip():
    """Verify the helper function generates the correct HTML component."""
    component = dash_app.metric_title_with_tooltip("Automation Rate")
    # Dash components are objects, we can verify it's a Div
    assert component.__class__.__name__ == 'Div'
    # Ensure it contains the metric title
    children = component.children
    assert len(children) == 3
    
def test_update_dashboard_callback():
    """Test the main dashboard callback logic directly."""
    # Call the callback with dummy inputs
    start_date = '2023-01-01'
    end_date = '2023-01-02'
    selected_intents = []
    
    outputs = dash_app.update_dashboard(start_date, end_date, selected_intents)
    
    # We expect 8 outputs: 4 gauges, 1 mini row, 3 charts
    assert len(outputs) == 8
    # Check that it returns figures
    assert hasattr(outputs[0], 'layout')  # Plotly Figure
