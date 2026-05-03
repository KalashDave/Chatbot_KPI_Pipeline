"""
Dash application for the primary interactive dashboard.
This file contains the layout, UI components, and all reactive callbacks
necessary to render the cyberpunk-themed analytics interface.
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from pathlib import Path

# --- Data Loading ---
# Resolve the path to the local SQLite database containing our engineered metrics
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chatbot_metrics.sqlite"

def load_data():
    """
    Connects to SQLite, reads the metrics table into a pandas DataFrame, 
    and handles data type conversions (datetimes and booleans).
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM metrics", conn)
        
        # Convert timestamp strings back to datetime objects for filtering
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # SQLite stores booleans as integers (0/1). Cast them back to bool.
        bool_cols = ['human_takeover', 'is_fallback', 'is_resolved', 'would_be_ticket', 'converted']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        return df

# Execute the data load once when the app boots up
df = load_data()

# --- Global Design Tokens ---
# These hex codes represent the OTA (Online Travel Agency) cyberpunk brand guidelines
FH_DARK = "#0F2A55"     # Dark background color
FH_LIGHT = "#23ADE0"    # Primary neon blue for charts and accents
FH_GREEN = "#2ECC71"    # Success green for positive metrics
FH_RED = "#E74C3C"      # Danger red for failure metrics

# --- Application Initialization ---
# Initialize the Dash app with the Bootstrap CYBORG theme for the dark-mode aesthetic
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "OTA Intelligence Dashboard"
# Expose the underlying Flask server for Gunicorn deployment (e.g. on Render)
server = app.server

# Metrics Metadata for Tooltips
metrics_info = {
    "Automation Rate": {"What it is": "The percentage of inquiries resolved entirely by the AI without human intervention.", "Why it matters": "High automation directly reduces support costs and scales operations.", "Benchmark": "70-85% for well-optimized systems."},
    "First Contact Resolution": {"What it is": "Percentage of issues successfully resolved on the very first interaction.", "Why it matters": "A high FCR means the chatbot is actually helpful, rather than just deflecting customers who later return frustrated.", "Benchmark": "> 65%"},
    "Customer Satisfaction": {"What it is": "The percentage of positive ratings (4 or 5 stars) given by users after a chat.", "Why it matters": "Efficiency metrics (like Automation) mean nothing if the customer experience is poor.", "Benchmark": "> 80%"},
    "Ticket Deflection": {"What it is": "The percentage of conversations that would have become support tickets but were resolved by the AI.", "Why it matters": "This is the strongest indicator of direct ROI and cost savings.", "Benchmark": "> 50%"},
    "Volume": {"What it is": "The total number of chatbot interactions over the selected period.", "Why it matters": "Indicates user adoption. A growing trend means customers trust the widget.", "Benchmark": "Steadily growing."},
    "Average Handling Time": {"What it is": "The average duration of a chat from start to finish.", "Why it matters": "Too short may indicate frustration/drop-offs; too long indicates a confusing conversation loop.", "Benchmark": "2-5 minutes."},
    "Human Takeover Rate": {"What it is": "How often a conversation is escalated to a live human agent.", "Why it matters": "Identifies the limitations of the AI's current knowledge base.", "Benchmark": "< 25%"},
    "Fallback Rate": {"What it is": "How often the AI fails to understand the user's intent entirely.", "Why it matters": "A high fallback rate indicates a poorly trained NLP model or confusing user queries.", "Benchmark": "< 10%"},
    "Conversion Rate": {"What it is": "The percentage of users who complete a desired action (like booking or purchasing) via the bot.", "Why it matters": "Shows the chatbot's value as a revenue-generating channel, not just a cost-center.", "Benchmark": "5-15%"},
    "Return Users": {"What it is": "The percentage of users who engage with the chatbot on multiple different occasions.", "Why it matters": "A high return rate proves the chatbot provides genuine utility and earns user trust.", "Benchmark": "> 30%"}
}

def metric_title_with_tooltip(title):
    """
    Generates a standardized HTML header for the mini-metric cards.
    It takes the raw title, looks up its corresponding definition and benchmarks
    from the metrics_info dictionary, and attaches an interactive info tooltip.
    """
    info = metrics_info[title]
    
    # Construct the rich HTML content for the tooltip pop-over
    tooltip_content = [
        html.Div([html.Strong("What it is: ", style={"color": "#23ADE0"}), html.Span(info["What it is"])]),
        html.Div([html.Strong("Why it matters: ", style={"color": "#2ECC71"}), html.Span(info["Why it matters"])], style={"marginTop": "8px"}),
        html.Div([html.Strong("Benchmark: ", style={"color": "#f59e0b"}), html.Span(info["Benchmark"])], style={"marginTop": "8px"})
    ]
    
    # Return a Flexbox container that centers the title but anchors the 'i' icon to the far right
    return html.Div([
        html.Div(style={"flex": "1"}), # Empty spacer to balance the left side
        html.Span(title, className="metric-title", style={"flex": "4", "textAlign": "center", "fontSize": "0.8rem", "lineHeight": "1.2"}),
        html.Div([
            # The 'i' icon that users hover over
            html.I(className="bi bi-info-circle", id=f"tooltip-{title.replace(' ', '-')}", style={"color": "#8b949e", "cursor": "help", "fontSize": "1rem"}),
            # The actual Tooltip component bound to the icon's ID
            dbc.Tooltip(tooltip_content, target=f"tooltip-{title.replace(' ', '-')}", placement="top", style={"textAlign": "left", "maxWidth": "350px", "fontSize": "0.85rem"})
        ], style={"flex": "1", "textAlign": "right"})
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "flex-start", "marginBottom": "5px", "width": "100%"})

app.layout = html.Div([
    html.Div([
        html.H1("CUSTOMER SERVICE CHATBOT PERFORMANCE HUB", className="cyber-title", style={"textAlign": "center"}),
        html.P("Tracking automated resolutions and customer satisfaction at scale.", style={"color": "#8b949e", "fontSize": "1.1rem", "marginBottom": "2rem", "textAlign": "center"}),
        
        # Top Filters
        dbc.Row([
            dbc.Col([
                html.P("Date Range", className="metric-title"),
                html.Div(
                    dcc.DatePickerRange(
                        id='date-picker',
                        min_date_allowed=df['timestamp'].min().date(),
                        max_date_allowed=df['timestamp'].max().date(),
                        start_date=df['timestamp'].min().date(),
                        end_date=df['timestamp'].max().date(),
                    ),
                    style={"color": "black"} # Force text black for standard white background
                )
            ], width=4),
            dbc.Col([
                html.P("Filter by Intent", className="metric-title"),
                html.Div(
                    dcc.Dropdown(
                        id='intent-dropdown',
                        options=[{'label': i, 'value': i} for i in df['intent'].dropna().unique()],
                        multi=True,
                        placeholder="All Intents"
                    ),
                    style={"color": "black"} # Force text black inside the react-select
                )
            ], width=8)
        ], style={"marginBottom": "2rem"}),
        
        # Top Row: Gauges
        dbc.Row([
            dbc.Col(html.Div([
                metric_title_with_tooltip("Automation Rate"),
                dcc.Graph(id='gauge-automation', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("First Contact Resolution"),
                dcc.Graph(id='gauge-fcr', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("Customer Satisfaction"),
                dcc.Graph(id='gauge-csat', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("Ticket Deflection"),
                dcc.Graph(id='gauge-deflection', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
        ], style={"marginBottom": "1.5rem"}),
        
        # Middle Row: Mini Metric Cards
        dbc.Row(id='mini-metrics-row', style={"marginBottom": "1.5rem"}),
        
        # Bottom Row: Large Visualizations
        dbc.Row([
            dbc.Col(html.Div([
                html.H4("Temporal Volume Dynamics", className="metric-title"),
                dcc.Graph(id='chart-timeline', config={'displayModeBar': False})
            ], className="glass-card"), width=6),
            
            dbc.Col(html.Div([
                html.H4("Handling Latency Map (Mins)", className="metric-title"),
                dcc.Graph(id='chart-intent-aht', config={'displayModeBar': False})
            ], className="glass-card"), width=6)
        ], style={"marginBottom": "2rem"}),
        
        # Failure Hotspots
        html.Div([
            html.H3("🚨 Failure Hotspots", style={"color": "white", "textAlign": "center"}),
            html.P("Intents that most frequently trigger Human Takeovers or Fallbacks.", style={"color": "#8b949e", "textAlign": "center", "marginBottom": "1.5rem"}),
            dcc.Graph(id='chart-failure-hotspots', config={'displayModeBar': False})
        ], className="glass-card", style={"marginBottom": "2rem"}),

        # Slice and Dice Custom Vis
        html.Div([
            html.H3("🔎 Custom Visualizations", style={"color": "white", "textAlign": "center"}),
            html.P("Select a grouping variable and a KPI metric to dynamically generate analytical charts.", style={"color": "#8b949e", "textAlign": "center", "marginBottom": "1.5rem"}),
            dbc.Row([
                dbc.Col([
                    html.P("Select X-Axis (Grouping)", className="metric-title", style={"color": "white"}),
                    dbc.Select(
                        id='custom-x', 
                        options=[
                            {'label': 'Intent', 'value': 'Intent'},
                            {'label': 'Date', 'value': 'Date'},
                            {'label': 'Day of Week', 'value': 'Day of Week'},
                            {'label': 'Hour of Day', 'value': 'Hour of Day'}
                        ], 
                        value='Intent'
                    )
                ], width=6),
                dbc.Col([
                    html.P("Select Y-Axis (Metric)", className="metric-title", style={"color": "white"}),
                    dbc.Select(
                        id='custom-y', 
                        options=[
                            {'label': 'Automation Rate', 'value': 'Automation Rate'},
                            {'label': 'First Contact Resolution', 'value': 'First Contact Resolution'},
                            {'label': 'Customer Satisfaction', 'value': 'Customer Satisfaction'},
                            {'label': 'Human Takeover Rate', 'value': 'Human Takeover Rate'},
                            {'label': 'Fallback Rate', 'value': 'Fallback Rate'},
                            {'label': 'Average Handling Time', 'value': 'Average Handling Time'},
                            {'label': 'Volume', 'value': 'Volume'}
                        ], 
                        value='Average Handling Time'
                    )
                ], width=6)
            ]),
            dcc.Graph(id='custom-chart', style={"marginTop": "1rem"})
        ], className="glass-card", style={"marginBottom": "2rem"}),
        
    ], style={"padding": "2.5rem", "maxWidth": "1400px", "margin": "0 auto"})
])

# --- Application Callback ---
# This single, monolithic callback listens to any changes in the Top Filters
# (Date Range or Intents) and automatically recalculates ALL metrics and charts.
@app.callback(
    [Output('gauge-automation', 'figure'),
     Output('gauge-fcr', 'figure'),
     Output('gauge-csat', 'figure'),
     Output('gauge-deflection', 'figure'),
     Output('mini-metrics-row', 'children'),
     Output('chart-timeline', 'figure'),
     Output('chart-intent-aht', 'figure'),
     Output('chart-failure-hotspots', 'figure')],
    [Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('intent-dropdown', 'value')]
)
def update_dashboard(start_date, end_date, selected_intents):
    """
    Triggered whenever a user changes a filter. 
    It slices the global dataframe down to match the user's selection, 
    re-runs the math, and returns the updated Plotly figures.
    """
    
    # --- Step 1: Apply Global Filters ---
    # Filter by Date Range
    mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & \
           (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
           
    # Filter by Intent (if any specific intents were selected)
    if selected_intents:
        mask = mask & (df['intent'].isin(selected_intents))
        
    # Create the final filtered working dataframe
    dff = df[mask]
    
    # --- Step 2: Recalculate KPIs ---
    # Return empty figures if the user's filters eliminated all data
    if dff.empty:
        return [go.Figure()] * 4 + [[]] + [go.Figure()] * 3
        
    # Core Volume
    total = len(dff)
    
    # Efficiency & Quality Calculations (Percentages)
    automation_rate = ((~dff['human_takeover']).sum() / total) * 100
    fcr = (dff['is_resolved'].sum() / total) * 100
    csat = ((dff['csat_score'] >= 4).sum() / total) * 100
    
    # Deflection Rate requires comparing tickets prevented vs tickets possible
    tickets_prevented = (dff['would_be_ticket'] & dff['is_resolved'] & ~dff['human_takeover']).sum()
    total_potential = dff['would_be_ticket'].sum()
    deflection_rate = (tickets_prevented / total_potential) * 100 if total_potential > 0 else 0
    
    # Operational metrics
    takeover_rate = (dff['human_takeover'].sum() / total) * 100
    fallback_rate = (dff['is_fallback'].sum() / total) * 100
    aht_mins = dff['average_handling_time'].mean() / 60
    conv_rate = (dff['converted'].sum() / total) * 100
    
    # User metrics
    user_counts = dff['user_id'].value_counts()
    ret_rate = ((user_counts > 1).sum() / len(user_counts)) * 100 if len(user_counts) > 0 else 0
    
    # --- Step 3: Build the UI Components ---
    def create_gauge(value, color):
        """
        Helper to construct a Plotly Gauge chart for the top row.
        """
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            number = {'suffix': "%", 'font': {'color': 'white', 'size': 36, 'family': 'Inter'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.1)", 'visible': False},
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': "rgba(255,255,255,0.05)",
                'borderwidth': 0,
                'shape': 'angular'
            }
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10, b=10, l=10, r=10), height=150)
        return fig
        
    g1 = create_gauge(automation_rate, FH_LIGHT)
    g2 = create_gauge(fcr, FH_LIGHT)
    g3 = create_gauge(csat, FH_GREEN)
    g4 = create_gauge(deflection_rate, FH_GREEN)
    
    def mini_card(key, value_str, value_num, max_val, color):
        # Progress bar logic
        prog_val = (value_num / max_val * 100) if max_val > 0 else 0
        prog_val = min(max(prog_val, 0), 100) # clamp
        
        return dbc.Col(html.Div([
            metric_title_with_tooltip(key),
            html.Div([
                html.Div(value_str, className="metric-value", style={"color": "white", "fontSize": "2rem"}),
                dbc.Progress(value=prog_val, color=color, style={"height": "4px", "backgroundColor": "rgba(255,255,255,0.1)", "marginTop": "10px"})
            ], style={"marginTop": "auto"})
        ], className="glass-card", style={"padding": "1rem", "textAlign": "center", "display": "flex", "flexDirection": "column"}), width=2)
        
    # Assuming volume max is around max daily volume, but we'll cap it dynamically
    vol_max = total * 1.5 if total > 0 else 1
    aht_max = 10 # 10 mins
    
    mini_row = [
        mini_card("Volume", f"{total:,}", total, vol_max, FH_LIGHT),
        mini_card("Average Handling Time", f"{aht_mins:.1f}m", aht_mins, aht_max, FH_LIGHT),
        mini_card("Human Takeover Rate", f"{takeover_rate:.1f}%", takeover_rate, 100, FH_RED),
        mini_card("Fallback Rate", f"{fallback_rate:.1f}%", fallback_rate, 100, FH_RED),
        mini_card("Conversion Rate", f"{conv_rate:.1f}%", conv_rate, 100, FH_LIGHT),
        mini_card("Return Users", f"{ret_rate:.1f}%", ret_rate, 100, FH_GREEN)
    ]
    
    # Timeline Visualizer
    # Group the chats by day and count volume, and sum the takeovers
    daily = dff.groupby(dff['timestamp'].dt.date).agg(Vol=('timestamp', 'count'), Takeovers=('human_takeover', 'sum')).reset_index()
    fig_time = go.Figure()
    
    # Add Area line for Total Volume
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Vol'], mode='lines', name='Volume', line=dict(color=FH_LIGHT, width=3), fill='tozeroy', fillcolor=f'rgba(35, 173, 224, 0.1)'))
    
    # Add overlay line for Human Takeovers
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Takeovers'], mode='lines', name='Takeovers', line=dict(color=FH_RED, width=3)))
    
    # Apply standard theme configurations
    fig_time.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), margin=dict(t=20, b=20, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=350)
    
    # --- Step 4: Build Handling Latency Box Plot ---
    # Box plot representing the statistical distribution of handling times.
    # Because there could be 100+ intents, we limit this chart to the Top 10 by volume to avoid clutter.
    dff_aht = dff.copy()
    dff_aht['AHT_Mins'] = dff_aht['average_handling_time'] / 60
    
    top_intents = dff_aht['intent'].value_counts().nlargest(10).index
    dff_aht = dff_aht[dff_aht['intent'].isin(top_intents)]
    
    fig_aht = px.box(dff_aht, x='AHT_Mins', y='intent', color_discrete_sequence=[FH_LIGHT], points="outliers")
    fig_aht.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Handling Time (Mins)"), yaxis=dict(title=""), margin=dict(t=10, b=10, l=150, r=10), height=350)
    
    # Disable hover data on this specific chart to keep it clean
    fig_aht.update_traces(hoverinfo='none', hovertemplate=None)
    
    # --- Step 5: Build Failure Hotspots Stacked Bar ---
    # Groups intents by the sum of fallbacks and takeovers, stacking them to show total failures.
    fails = dff.groupby('intent').agg(
        Fallbacks=('is_fallback', 'sum'),
        Takeovers=('human_takeover', 'sum')
    ).reset_index()
    
    # Sum them to sort and find the absolute worst performing intents
    fails['Total Failures'] = fails['Fallbacks'] + fails['Takeovers']
    fails = fails.sort_values(by='Total Failures', ascending=True).tail(10)
    
    fig_hotspots = go.Figure()
    fig_hotspots.add_trace(go.Bar(y=fails['intent'], x=fails['Fallbacks'], name='Fallbacks', orientation='h', marker_color='#f59e0b'))
    fig_hotspots.add_trace(go.Bar(y=fails['intent'], x=fails['Takeovers'], name='Takeovers', orientation='h', marker_color=FH_RED))
    
    # 'barmode=stack' stacks the orange and red bars on top of each other
    fig_hotspots.update_layout(barmode='stack', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Failure Count"), yaxis=dict(title=""), margin=dict(t=10, b=10, l=150, r=10), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    # Return everything back to the Dash UI in the exact order requested by the Outputs
    return g1, g2, g3, g4, mini_row, fig_time, fig_aht, fig_hotspots

# --- Secondary Callback: Custom Viz Engine ---
# This callback powers the dynamic dropdowns at the bottom of the dashboard.
@app.callback(
    Output('custom-chart', 'figure'),
    [Input('custom-x', 'value'), Input('custom-y', 'value'), Input('date-picker', 'start_date'), Input('date-picker', 'end_date'), Input('intent-dropdown', 'value')]
)
def update_custom(x_axis, y_axis, start_date, end_date, selected_intents):
    """
    Takes the user's custom X and Y axis selections, infers the data types,
    and dynamically groups/aggregates the dataset to generate a custom chart.
    """
    if not x_axis or not y_axis:
        return go.Figure().update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
    mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
    if selected_intents:
        mask = mask & (df['intent'].isin(selected_intents))
    plot_df = df[mask].copy()
    
    if plot_df.empty:
        return go.Figure()

    # --- Step 1: Determine Grouping Variable (X) ---
    # We map the user's plain-text dropdown selection to the actual dataframe column/datetime extraction
    if x_axis == 'Intent':
        plot_df['Group'] = plot_df['intent']
    elif x_axis == 'Date':
        plot_df['Group'] = plot_df['timestamp'].dt.date
    elif x_axis == 'Day of Week':
        plot_df['Group'] = plot_df['timestamp'].dt.day_name()
    elif x_axis == 'Hour of Day':
        plot_df['Group'] = plot_df['timestamp'].dt.hour
        
    # --- Step 2: Aggregate Metrics (Y) ---
    # Based on the selected KPI, we group by the newly created 'Group' column and run the specific math.
    if y_axis == 'Automation Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: ((~x['human_takeover']).sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'First Contact Resolution':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['is_resolved'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Customer Satisfaction':
        agg_df = plot_df.groupby('Group').apply(lambda x: ((x['csat_score'] >= 4).sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Human Takeover Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['human_takeover'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Fallback Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['is_fallback'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Average Handling Time':
        agg_df = plot_df.groupby('Group')['average_handling_time'].mean().reset_index(name='Val')
        # Convert seconds to minutes for readability
        agg_df['Val'] /= 60
    elif y_axis == 'Volume':
        # Volume is just a simple count of rows per group
        agg_df = plot_df.groupby('Group').size().reset_index(name='Val')
        
    # --- Step 3: Select Chart Type ---
    # If the X-Axis is time-based, we render a Line Chart. If categorical, a Bar Chart.
    if x_axis == 'Date':
        agg_df = agg_df.sort_values('Group')
        fig = px.line(agg_df, x='Group', y='Val', title=f"{y_axis} over {x_axis}", color_discrete_sequence=[FH_LIGHT])
    elif x_axis == 'Hour of Day':
        agg_df = agg_df.sort_values('Group')
        fig = px.line(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT], markers=True)
    elif x_axis == 'Day of Week':
        # Force the days to sort chronologically rather than alphabetically
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        agg_df['Group'] = pd.Categorical(agg_df['Group'], categories=days, ordered=True)
        agg_df = agg_df.sort_values('Group')
        fig = px.bar(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT])
    else:
        # Fallback for 'Intent' or other categoricals. Sort by highest value and limit to top 15.
        agg_df = agg_df.sort_values(by='Val', ascending=False).head(15)
        fig = px.bar(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT])
        fig.update_layout(xaxis={'categoryorder':'total descending'})

    # Apply global chart styling to match the dark cyberpunk theme
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=x_axis), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=y_axis))
    
    return fig

if __name__ == '__main__':
    app.run(debug=False, port=8050)
