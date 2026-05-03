"""
Streamlit application for the dashboard.
This provides the lightweight, rapid-prototyping "Operational Dashboard" frontend.
It connects to the same local SQLite database as the Dash app.
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path

# --- Configuration & Paths ---
# Resolve the path to the local SQLite database
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chatbot_metrics.sqlite"

# --- Page Configuration ---
# Must be the very first Streamlit command. Sets the browser tab title and layout width.
st.set_page_config(page_title="OTA Intelligence Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- OTA Theme Configuration ---
bg_color = "#F4F7F9"
card_bg = "#FFFFFF"
text_color = "#0F2A55" # Blue Zodiac
sub_text = "#475569"
border_color = "rgba(15, 42, 85, 0.1)"
hover_border = "#23ADE0" # Curious Blue
tooltip_bg = "#0F2A55"
tooltip_color = "#FFFFFF"

# SVG Tooltip Icon
INFO_SVG = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #94A3B8; margin-top: 2px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'

# Custom CSS
st.markdown(f"""
<style>
    /* Force Background and Text Colors */
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
    }}
    
    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {card_bg};
        border-right: 1px solid {border_color};
    }}
    
    /* Hide Anchor Icons (Chain Links) */
    .stMarkdown a.header-anchor, .stMarkdown a.header-anchor:hover {{
        display: none !important;
    }}
    
    /* Text Color Fixes for Streamlit Native Elements */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown p, .stMarkdown li, .stSelectbox label {{
        color: {text_color} !important;
    }}
    
    .metric-card {{
        background: {card_bg};
        border-radius: 12px;
        padding: 20px;
        border: 1px solid {border_color};
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        transition: transform 0.2s ease-in-out;
        position: relative;
    }}
    
    .metric-card:hover {{
        transform: translateY(-5px);
        border-color: {hover_border};
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    }}
    
    /* Progress bar container */
    .progress-container {{
        width: 100%;
        background-color: {border_color};
        border-radius: 4px;
        height: 6px;
        margin-top: 10px;
    }}
    
    /* Tooltip container */
    .tooltip {{
        position: absolute;
        top: 20px;
        right: 20px;
        cursor: pointer;
        display: inline-block;
    }}

    .tooltip .tooltiptext {{
        visibility: hidden;
        width: 260px;
        background-color: {tooltip_bg};
        color: {tooltip_color};
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 999;
        bottom: 125%;
        left: 50%;
        margin-left: -130px;
        opacity: 0;
        transition: opacity 0.3s;
        font-size: 13px;
        line-height: 1.5;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}

    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    
    /* Gradient Title */
    .gradient-title {{
        background: -webkit-linear-gradient(45deg, #0F2A55, #23ADE0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 54px;
        font-weight: 800;
        text-align: center;
        margin-bottom: 5px;
    }}
    .subtitle {{
        text-align: center;
        color: {sub_text};
        font-size: 20px;
        margin-bottom: 40px;
    }}
</style>
""", unsafe_allow_html=True)

def make_metric_card(title, value, description, benchmark, icon, bar_color, progress_pct):
    """
    Helper function to generate the raw HTML/CSS for a highly styled metric card.
    Streamlit's native metrics are very basic, so we use custom HTML to get
    hover animations, tooltips, and progress bars.
    """
    # Ensure progress_pct is strictly bounded between 0 and 100 for the CSS width property
    safe_pct = max(0, min(100, progress_pct))
    
    # Construct the HTML block. Deep indentation is avoided so Streamlit's 
    # Markdown parser doesn't incorrectly interpret it as a code block.
    return f"""<div class="metric-card">
<div class="tooltip">{INFO_SVG}
<span class="tooltiptext"><b>{title}</b><br/><br/>{description}<br/><br/><i>Benchmark: {benchmark}</i></span>
</div>
<h4 style="color: {sub_text}; margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; display: flex; align-items: center; gap: 8px;">
<span>{icon}</span> {title}
</h4>
<h2 style="color: {text_color}; margin: 10px 0 5px 0; font-size: 32px; font-weight: bold; font-family: 'Inter', sans-serif;">
{value}
</h2>
<div class="progress-container">
<div style="width: {safe_pct}%; background-color: {bar_color}; height: 100%; border-radius: 4px;"></div>
</div>
</div>"""

# Cache the data loading function so Streamlit doesn't repeatedly query the DB 
# on every single button click or slider movement (TTL = 3600 seconds / 1 hour)
@st.cache_data(ttl=3600)
def load_data():
    """
    Connects to the local SQLite database and loads the metrics table into memory.
    """
    if not DB_PATH.exists():
        # Stop execution and warn the user if the DB hasn't been built yet
        st.error("Database not found. Please run the pipeline.")
        return pd.DataFrame()
        
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM metrics", conn)
        
        # Cast the timestamp strings back into pandas datetime objects
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # SQLite stores booleans as integers (0/1). Cast them back to bool for pandas operations.
        bool_cols = ['human_takeover', 'is_fallback', 'is_resolved', 'would_be_ticket', 'converted']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        return df

# Execute the data load
df = load_data()

# Halt the entire app if the dataframe is empty to prevent cascading errors
if df.empty:
    st.stop()

# --- Title Redesign ---
st.markdown("<h1 class='gradient-title'>OTA Intelligence Dashboard</h1>", unsafe_allow_html=True)
st.markdown(f"<p class='subtitle'>Real-time Interactive Intelligence Dashboard</p>", unsafe_allow_html=True)

# --- Sidebar Filters ---
st.sidebar.markdown("---")
st.sidebar.header("Filters")

# Find the absolute min and max dates in the dataset to set the calendar widget bounds
min_date = df['timestamp'].min().date()
max_date = df['timestamp'].max().date()

# Render the date range input widget
date_range = st.sidebar.date_input("Select Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

# Handle cases where the user has only clicked one date so far (Streamlit returns a tuple of length 1)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = min_date
    end_date = max_date

# Extract all unique intents for the multi-select dropdown
intents = df['intent'].dropna().unique().tolist()
selected_intents = st.sidebar.multiselect("Filter by Intent", options=intents, default=[])

# --- Apply Filters to DataFrame ---
# Filter 1: Keep only rows within the selected date range
mask = (df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)

# Filter 2: If the user selected specific intents, filter out unselected intents
if selected_intents:
    mask = mask & (df['intent'].isin(selected_intents))
    
# Apply the boolean mask to generate the final filtered dataframe
filtered_df = df[mask]

# If the user filtered out literally everything, stop rendering the UI and show a warning
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# --- KPI Calculations ---
# All calculations are performed dynamically on the `filtered_df` so they
# react instantly whenever the user changes a date or intent filter.

# Total volume of conversations in the filtered set
total_chats = len(filtered_df)

# Automation Rate: Chats that were NEVER taken over by a human
automated_chats = (~filtered_df['human_takeover']).sum()
automation_rate = (automated_chats / total_chats) * 100 if total_chats > 0 else 0

# Resolution Rate (FCR): Chats successfully resolved
resolved_chats = filtered_df['is_resolved'].sum()
resolution_rate = (resolved_chats / total_chats) * 100 if total_chats > 0 else 0

# Human Takeover Rate: Chats escalated to a live agent
takeover_rate = (filtered_df['human_takeover'].sum() / total_chats) * 100 if total_chats > 0 else 0

# Fallback Rate: Chats where the AI completely failed to understand intent
fallback_rate = (filtered_df['is_fallback'].sum() / total_chats) * 100 if total_chats > 0 else 0

# Average Handling Time: Convert seconds to a readable minutes format
aht_seconds = filtered_df['average_handling_time'].mean()
aht_minutes = aht_seconds / 60

# CSAT Score: Percentage of ratings that are strictly 4 or 5 stars
positive_csat = (filtered_df['csat_score'] >= 4).sum()
csat_percentage = (positive_csat / total_chats) * 100 if total_chats > 0 else 0

# Return Visitor Rate: Identify users with more than 1 interaction in this timeframe
user_counts = filtered_df['user_id'].value_counts()
returning_users = (user_counts > 1).sum()
total_unique_users = len(user_counts)
return_visitor_rate = (returning_users / total_unique_users) * 100 if total_unique_users > 0 else 0

# Conversion Rate: Chats resulting in a desired action (e.g., sale, booking)
conversions = filtered_df['converted'].sum()
conversion_rate = (conversions / total_chats) * 100 if total_chats > 0 else 0

# Ticket Deflection: Chats that were highly complex AND resolved by the AI
tickets_prevented = (filtered_df['would_be_ticket'] & filtered_df['is_resolved'] & ~filtered_df['human_takeover']).sum()
total_potential_tickets = filtered_df['would_be_ticket'].sum()
ticket_deflection_rate = (tickets_prevented / total_potential_tickets) * 100 if total_potential_tickets > 0 else 0

# Define Dictionary of Metrics
metrics_dict = {
    "Automation Rate": {
        "value": f"{automation_rate:.1f}%", "progress_pct": automation_rate, "bar_color": "#23ADE0", "icon": "⚡",
        "description": "Percentage of all incoming customer enquiries your chatbot resolves completely without human intervention.",
        "benchmark": "70–85%"
    },
    "Resolution Rate": {
        "value": f"{resolution_rate:.1f}%", "progress_pct": resolution_rate, "bar_color": "#23ADE0", "icon": "✅",
        "description": "Percentage of enquiries that were actually resolved by the bot without needing to resubmit.",
        "benchmark": "> 65%"
    },
    "Takeover Rate": {
        "value": f"{takeover_rate:.1f}%", "progress_pct": takeover_rate, "bar_color": "#E11D48", "icon": "🧑‍💻",
        "description": "Shows how often a chatbot has to hand a conversation over to a human agent.",
        "benchmark": "< 25%"
    },
    "Fallback Rate": {
        "value": f"{fallback_rate:.1f}%", "progress_pct": fallback_rate, "bar_color": "#E11D48", "icon": "⚠️",
        "description": "How often the chatbot was unable to understand an enquiry and responded with a generic error.",
        "benchmark": "< 10%"
    },
    "Avg Handling Time": {
        "value": f"{aht_minutes:.1f} m", "progress_pct": min((aht_minutes/10)*100, 100), "bar_color": "#23ADE0", "icon": "⏱️",
        "description": "How long a chatbot conversation takes on average.",
        "benchmark": "2–5 min"
    },
    "CSAT Score": {
        "value": f"{csat_percentage:.1f}%", "progress_pct": csat_percentage, "bar_color": "#2ECC71", "icon": "⭐",
        "description": "Measures how satisfied users were with their chatbot conversation based on positive ratings.",
        "benchmark": "> 80%"
    },
    "Return Visitors": {
        "value": f"{return_visitor_rate:.1f}%", "progress_pct": return_visitor_rate, "bar_color": "#23ADE0", "icon": "🔄",
        "description": "How many users voluntarily use the chatbot a second time or more.",
        "benchmark": "> 30%"
    },
    "Conversation Volume": {
        "value": f"{total_chats:,}", "progress_pct": 100, "bar_color": "#23ADE0", "icon": "📊",
        "description": "Total number of chatbot conversations in the selected period.",
        "benchmark": "Growing Trend"
    },
    "Conversion Rate": {
        "value": f"{conversion_rate:.1f}%", "progress_pct": conversion_rate, "bar_color": "#F59E0B", "icon": "🛒",
        "description": "How often the chatbot triggers a desired action (e.g. demo booking, purchase).",
        "benchmark": "5–15%"
    },
    "Ticket Deflection": {
        "value": f"{ticket_deflection_rate:.1f}%", "progress_pct": ticket_deflection_rate, "bar_color": "#2ECC71", "icon": "🛡️",
        "description": "How many support tickets were prevented by the chatbot.",
        "benchmark": "> 50%"
    }
}

# --- Layout ---
st.markdown(f"<h3>⚙️ Efficiency</h3>", unsafe_allow_html=True)
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.markdown(make_metric_card("Automation Rate", **metrics_dict["Automation Rate"]), unsafe_allow_html=True)
with col2: st.markdown(make_metric_card("Resolution Rate", **metrics_dict["Resolution Rate"]), unsafe_allow_html=True)
with col3: st.markdown(make_metric_card("Takeover Rate", **metrics_dict["Takeover Rate"]), unsafe_allow_html=True)
with col4: st.markdown(make_metric_card("Fallback Rate", **metrics_dict["Fallback Rate"]), unsafe_allow_html=True)
with col5: st.markdown(make_metric_card("Avg Handling Time", **metrics_dict["Avg Handling Time"]), unsafe_allow_html=True)

st.markdown(f"<h3>👥 Customer Experience</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1: st.markdown(make_metric_card("CSAT Score", **metrics_dict["CSAT Score"]), unsafe_allow_html=True)
with col2: st.markdown(make_metric_card("Return Visitors", **metrics_dict["Return Visitors"]), unsafe_allow_html=True)
with col3: st.markdown(make_metric_card("Conversation Volume", **metrics_dict["Conversation Volume"]), unsafe_allow_html=True)

st.markdown(f"<h3>💼 Business Impact</h3>", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1: st.markdown(make_metric_card("Conversion Rate", **metrics_dict["Conversion Rate"]), unsafe_allow_html=True)
with col2: st.markdown(make_metric_card("Ticket Deflection", **metrics_dict["Ticket Deflection"]), unsafe_allow_html=True)

# Sleek ROI Insight Placement
saved_hours = (tickets_prevented * 10) / 60
st.markdown(f"<p style='color: {sub_text}; font-size: 14px; font-style: italic; margin-top: -10px; margin-bottom: 30px;'>💡 <b>ROI Insight:</b> Deflecting {tickets_prevented:,} tickets saved approximately <b>{saved_hours:,.0f} hours</b> of human agent time in this period.</p>", unsafe_allow_html=True)

st.markdown("---")

# --- Dynamic Deep Dive Visualizations ---
st.markdown(f"<h2 style='text-align: center; margin-bottom: 20px; color: {text_color};'>🔎 Custom Visualizations</h2>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align: center; color: {sub_text}; margin-top: -15px; margin-bottom: 20px;'>Select any two metrics to dynamically generate a chart based on their data types.</p>", unsafe_allow_html=True)

col_x, col_y = st.columns(2)

# Determine safe default indices for the dropdowns
cols_list = list(filtered_df.columns)
idx_x = cols_list.index('intent') if 'intent' in cols_list else 0
idx_y = cols_list.index('average_handling_time') if 'average_handling_time' in cols_list else min(1, len(cols_list)-1)

with col_x:
    x_col = st.selectbox("Select X-Axis", cols_list, index=idx_x)
with col_y:
    y_col = st.selectbox("Select Y-Axis", cols_list, index=idx_y)

try:
    if x_col == y_col:
        # Prevent plotting the same metric against itself
        st.warning("Please select different columns for X and Y axes to generate a comparison chart.")
    else:
        # --- Chart Type Inference Engine ---
        # Determine the data types of the selected columns to automatically 
        # pick the correct mathematical aggregation and Plotly chart type.
        x_is_datetime = pd.api.types.is_datetime64_any_dtype(filtered_df[x_col])
        y_is_numeric = pd.api.types.is_numeric_dtype(filtered_df[y_col])
        x_is_numeric = pd.api.types.is_numeric_dtype(filtered_df[x_col])
        
        # Build an isolated dataframe for plotting to avoid altering the global filtered_df
        plot_df = filtered_df[[x_col, y_col]].copy()
        
        # If plotting against time, extract just the date.
        # Plotting against raw seconds/timestamps would crash the browser with too many data points.
        plot_x = x_col
        if x_is_datetime:
            plot_df['_x_date'] = plot_df[x_col].dt.date
            plot_x = '_x_date'

        plot_y = y_col
        if pd.api.types.is_datetime64_any_dtype(plot_df[y_col]):
             plot_df['_y_date'] = plot_df[y_col].dt.date
             plot_y = '_y_date'

        # --- Dynamic Chart Builder ---
        if x_is_datetime and y_is_numeric:
            # Date vs Numeric -> Generate a Time Series Line Chart (averaging the numeric value per day)
            viz_df = plot_df.groupby(plot_x)[plot_y].mean().reset_index()
            fig = px.line(viz_df, x=plot_x, y=plot_y, title=f"Average {y_col} over Time", color_discrete_sequence=['#23ADE0'])
            
        elif not x_is_numeric and not x_is_datetime and y_is_numeric:
            # Categorical vs Numeric -> Generate a Bar Chart (averaging the numeric value per category)
            viz_df = plot_df.groupby(plot_x)[plot_y].mean().reset_index().sort_values(by=plot_y, ascending=False).head(15)
            fig = px.bar(viz_df, x=plot_x, y=plot_y, title=f"Average {y_col} by {x_col}", color_discrete_sequence=['#23ADE0'])
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            
        elif x_is_numeric and y_is_numeric:
            # Numeric vs Numeric -> Generate a Scatter Plot
            # Sample down to 2000 points max to ensure the browser doesn't freeze rendering thousands of dots
            sample_df = plot_df.sample(min(2000, len(plot_df)))
            fig = px.scatter(sample_df, x=plot_x, y=plot_y, title=f"{y_col} vs {x_col}", color_discrete_sequence=['#23ADE0'], opacity=0.5)
            
        else:
            # Categorical vs Categorical (or mixed bools) -> Generate a Count Stacked Bar Chart
            viz_df = plot_df.groupby([plot_x, plot_y]).size().reset_index(name='count')
            # Limit to top 10 categories if there are hundreds of permutations
            top_x = viz_df.groupby(plot_x)['count'].sum().nlargest(10).index
            viz_df = viz_df[viz_df[plot_x].isin(top_x)]
            fig = px.bar(viz_df, x=plot_x, y='count', color=plot_y, title=f"Count of {y_col} by {x_col}")

        # Apply standard theme configurations to the Plotly figure
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', 
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color),
            xaxis=dict(gridcolor=border_color),
            yaxis=dict(gridcolor=border_color)
        )
        
        # Render the chart into the Streamlit UI
        st.plotly_chart(fig, use_container_width=True)
        
        # --- Critical Anomaly Log ---
        st.markdown("---")
        st.markdown(f"<h2 style='text-align: center; margin-bottom: 10px; color: {text_color};'>🚨 Critical Anomaly Log</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: {sub_text}; margin-top: -15px; margin-bottom: 20px;'>Recent conversations requiring human takeover or resulting in a fallback.</p>", unsafe_allow_html=True)
        
        # Filter for recent failures and display them in a styled dataframe
        anomaly_df = filtered_df[filtered_df['human_takeover'] | filtered_df['is_fallback']].copy()
        anomaly_df = anomaly_df.sort_values(by='timestamp', ascending=False).head(8)
        
        if not anomaly_df.empty:
            display_cols = ['timestamp', 'user_id', 'intent', 'is_fallback', 'human_takeover', 'average_handling_time']
            # Highlight true fallbacks and takeovers in red
            st.dataframe(
                anomaly_df[display_cols].style.applymap(
                    lambda x: "background-color: #FEE2E2; color: #991B1B; font-weight: bold;" if x is True else "", 
                    subset=['is_fallback', 'human_takeover']
                ), 
                use_container_width=True
            )
        else:
            st.success("No anomalies detected in the selected period!")

except Exception as e:
    # Broad catch-all to prevent the entire dashboard from crashing if 
    # a strange data-type combination throws a plotting error.
    st.error(f"Could not render visualization for selected axes. Please try another combination.")
