import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlite3
from pathlib import Path

# Load Data
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chatbot_metrics.sqlite"
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT * FROM metrics", conn)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        bool_cols = ['human_takeover', 'is_fallback', 'is_resolved', 'would_be_ticket', 'converted']
        for col in bool_cols:
            if col in df.columns:
                df[col] = df[col].astype(bool)
        return df

df = load_data()

# OTA Colors
FH_DARK = "#0F2A55"
FH_LIGHT = "#23ADE0"
FH_GREEN = "#2ECC71"
FH_RED = "#E74C3C"

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "OTA Intelligence Dashboard"
server = app.server

# Metrics Metadata for Tooltips
metrics_info = {
    "Automation": "What percentage of enquiries the chatbot resolves completely without human intervention.\nBenchmark: 70-85%",
    "FCR": "First Contact Resolution. Were the enquiries actually resolved?\nBenchmark: > 65%",
    "CSAT": "Customer Satisfaction Score based on post-chat ratings.\nBenchmark: > 80%",
    "Deflection": "How many support tickets were prevented by the chatbot.\nBenchmark: > 50%",
    "Volume": "Total number of chatbot conversations in the selected period.\nBenchmark: Growing Trend",
    "Handling": "How long a chatbot conversation takes on average.\nBenchmark: 2-5 min",
    "Takeover": "Shows how often a chatbot has to hand a conversation over to a human agent.\nBenchmark: < 25%",
    "Fallback": "How often the chatbot was unable to understand an enquiry and responded with a generic error.\nBenchmark: < 10%",
    "Conversion": "How often the chatbot triggers a desired action (e.g. demo booking, purchase).\nBenchmark: 5-15%",
    "Return Users": "How many users voluntarily use the chatbot a second time or more.\nBenchmark: > 30%"
}

def metric_title_with_tooltip(title, icon):
    return html.Div([
        html.Span(f"{icon} {title}", className="metric-title", style={"marginBottom": "5px"}),
        html.I(className="bi bi-info-circle ms-2", id=f"tooltip-{title.replace(' ', '-')}", style={"color": "#8b949e", "cursor": "help"}),
        dbc.Tooltip(metrics_info[title], target=f"tooltip-{title.replace(' ', '-')}", placement="top", style={"whiteSpace": "pre-line"})
    ], style={"display": "flex", "justifyContent": "center", "alignItems": "center"})

app.layout = html.Div([
    html.Div([
        html.H1("INTELLIGENCE DASHBOARD", className="cyber-title", style={"textAlign": "center"}),
        html.P("Real-time telemetry and advanced KPI modeling.", style={"color": "#8b949e", "fontSize": "1.1rem", "marginBottom": "2rem", "textAlign": "center"}),
        
        # Top Filters
        dbc.Row([
            dbc.Col([
                html.P("Date Range", className="metric-title"),
                dcc.DatePickerRange(
                    id='date-picker',
                    min_date_allowed=df['timestamp'].min().date(),
                    max_date_allowed=df['timestamp'].max().date(),
                    start_date=df['timestamp'].min().date(),
                    end_date=df['timestamp'].max().date(),
                )
            ], width=4),
            dbc.Col([
                html.P("Filter by Intent", className="metric-title"),
                dcc.Dropdown(
                    id='intent-dropdown',
                    options=[{'label': i, 'value': i} for i in df['intent'].dropna().unique()],
                    multi=True,
                    placeholder="All Intents",
                    className="custom-dropdown"
                )
            ], width=8)
        ], style={"marginBottom": "2rem"}),
        
        # Top Row: Gauges
        dbc.Row([
            dbc.Col(html.Div([
                metric_title_with_tooltip("Automation", "🤖"),
                dcc.Graph(id='gauge-automation', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("FCR", "✅"),
                dcc.Graph(id='gauge-fcr', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("CSAT", "😊"),
                dcc.Graph(id='gauge-csat', config={'displayModeBar': False})
            ], className="glass-card"), width=3),
            dbc.Col(html.Div([
                metric_title_with_tooltip("Deflection", "🛡️"),
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
                    dcc.Dropdown(
                        id='custom-x', 
                        options=[
                            {'label': 'Intent', 'value': 'Intent'},
                            {'label': 'Date', 'value': 'Date'},
                            {'label': 'Day of Week', 'value': 'Day of Week'},
                            {'label': 'Hour of Day', 'value': 'Hour of Day'}
                        ], 
                        value='Intent', 
                        className="custom-dropdown"
                    )
                ], width=6),
                dbc.Col([
                    html.P("Select Y-Axis (Metric)", className="metric-title", style={"color": "white"}),
                    dcc.Dropdown(
                        id='custom-y', 
                        options=[
                            {'label': 'Automation Rate', 'value': 'Automation Rate'},
                            {'label': 'FCR', 'value': 'FCR'},
                            {'label': 'CSAT', 'value': 'CSAT'},
                            {'label': 'Takeover Rate', 'value': 'Takeover Rate'},
                            {'label': 'Fallback Rate', 'value': 'Fallback Rate'},
                            {'label': 'AHT (Mins)', 'value': 'AHT (Mins)'},
                            {'label': 'Volume', 'value': 'Volume'}
                        ], 
                        value='AHT (Mins)', 
                        className="custom-dropdown"
                    )
                ], width=6)
            ]),
            dcc.Graph(id='custom-chart', style={"marginTop": "1rem"})
        ], className="glass-card", style={"marginBottom": "2rem"}),
        
    ], style={"padding": "2.5rem", "maxWidth": "1400px", "margin": "0 auto"})
])

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
    mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & \
           (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
    if selected_intents:
        mask = mask & (df['intent'].isin(selected_intents))
    dff = df[mask]
    
    if dff.empty:
        return [go.Figure()] * 4 + [[]] + [go.Figure()] * 3
        
    total = len(dff)
    automation_rate = ((~dff['human_takeover']).sum() / total) * 100
    fcr = (dff['is_resolved'].sum() / total) * 100
    csat = ((dff['csat_score'] >= 4).sum() / total) * 100
    
    tickets_prevented = (dff['would_be_ticket'] & dff['is_resolved'] & ~dff['human_takeover']).sum()
    total_potential = dff['would_be_ticket'].sum()
    deflection_rate = (tickets_prevented / total_potential) * 100 if total_potential > 0 else 0
    
    takeover_rate = (dff['human_takeover'].sum() / total) * 100
    fallback_rate = (dff['is_fallback'].sum() / total) * 100
    aht_mins = dff['average_handling_time'].mean() / 60
    conv_rate = (dff['converted'].sum() / total) * 100
    
    user_counts = dff['user_id'].value_counts()
    ret_rate = ((user_counts > 1).sum() / len(user_counts)) * 100 if len(user_counts) > 0 else 0
    
    def create_gauge(value, color):
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
    
    def mini_card(key, value_str, value_num, max_val, color, icon):
        # Progress bar logic
        prog_val = (value_num / max_val * 100) if max_val > 0 else 0
        prog_val = min(max(prog_val, 0), 100) # clamp
        
        return dbc.Col(html.Div([
            metric_title_with_tooltip(key, icon),
            html.Div(value_str, className="metric-value", style={"color": "white", "fontSize": "2rem"}),
            dbc.Progress(value=prog_val, color=color, style={"height": "4px", "backgroundColor": "rgba(255,255,255,0.1)", "marginTop": "10px"})
        ], className="glass-card", style={"padding": "1rem", "textAlign": "center"}), width=2)
        
    # Assuming volume max is around max daily volume, but we'll cap it dynamically
    vol_max = total * 1.5 if total > 0 else 1
    aht_max = 10 # 10 mins
    
    mini_row = [
        mini_card("Volume", f"{total:,}", total, vol_max, FH_LIGHT, "📊"),
        mini_card("Handling", f"{aht_mins:.1f}m", aht_mins, aht_max, FH_LIGHT, "⏱️"),
        mini_card("Takeover", f"{takeover_rate:.1f}%", takeover_rate, 100, FH_RED, "🧑‍💻"),
        mini_card("Fallback", f"{fallback_rate:.1f}%", fallback_rate, 100, FH_RED, "⚠️"),
        mini_card("Conversion", f"{conv_rate:.1f}%", conv_rate, 100, FH_LIGHT, "🛒"),
        mini_card("Return Users", f"{ret_rate:.1f}%", ret_rate, 100, FH_GREEN, "🔄")
    ]
    
    # Timeline
    daily = dff.groupby(dff['timestamp'].dt.date).agg(Vol=('timestamp', 'count'), Takeovers=('human_takeover', 'sum')).reset_index()
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Vol'], mode='lines', name='Volume', line=dict(color=FH_LIGHT, width=3), fill='tozeroy', fillcolor=f'rgba(35, 173, 224, 0.1)'))
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Takeovers'], mode='lines', name='Takeovers', line=dict(color=FH_RED, width=3)))
    fig_time.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), margin=dict(t=20, b=20, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=350)
    
    # Box plot for AHT by Intent
    dff_aht = dff.copy()
    dff_aht['AHT_Mins'] = dff_aht['average_handling_time'] / 60
    # Top 10 intents by volume to avoid clutter
    top_intents = dff_aht['intent'].value_counts().nlargest(10).index
    dff_aht = dff_aht[dff_aht['intent'].isin(top_intents)]
    
    fig_aht = px.box(dff_aht, x='AHT_Mins', y='intent', color_discrete_sequence=[FH_LIGHT], points="outliers")
    fig_aht.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Handling Time (Mins)"), yaxis=dict(title=""), margin=dict(t=10, b=10, l=150, r=10), height=350)
    
    # Failure Hotspots
    fails = dff.groupby('intent').agg(
        Fallbacks=('is_fallback', 'sum'),
        Takeovers=('human_takeover', 'sum')
    ).reset_index()
    fails['Total Failures'] = fails['Fallbacks'] + fails['Takeovers']
    fails = fails.sort_values(by='Total Failures', ascending=True).tail(10)
    
    fig_hotspots = go.Figure()
    fig_hotspots.add_trace(go.Bar(y=fails['intent'], x=fails['Fallbacks'], name='Fallbacks', orientation='h', marker_color='#f59e0b'))
    fig_hotspots.add_trace(go.Bar(y=fails['intent'], x=fails['Takeovers'], name='Takeovers', orientation='h', marker_color=FH_RED))
    fig_hotspots.update_layout(barmode='stack', paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Failure Count"), yaxis=dict(title=""), margin=dict(t=10, b=10, l=150, r=10), height=350, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    return g1, g2, g3, g4, mini_row, fig_time, fig_aht, fig_hotspots

@app.callback(
    Output('custom-chart', 'figure'),
    [Input('custom-x', 'value'), Input('custom-y', 'value'), Input('date-picker', 'start_date'), Input('date-picker', 'end_date'), Input('intent-dropdown', 'value')]
)
def update_custom(x_axis, y_axis, start_date, end_date, selected_intents):
    if not x_axis or not y_axis:
        return go.Figure().update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
    mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
    if selected_intents:
        mask = mask & (df['intent'].isin(selected_intents))
    plot_df = df[mask].copy()
    
    if plot_df.empty:
        return go.Figure()

    # Determine Grouping Variable (X)
    if x_axis == 'Intent':
        plot_df['Group'] = plot_df['intent']
    elif x_axis == 'Date':
        plot_df['Group'] = plot_df['timestamp'].dt.date
    elif x_axis == 'Day of Week':
        plot_df['Group'] = plot_df['timestamp'].dt.day_name()
    elif x_axis == 'Hour of Day':
        plot_df['Group'] = plot_df['timestamp'].dt.hour
        
    # Aggregate Metrics (Y)
    if y_axis == 'Automation Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: ((~x['human_takeover']).sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'FCR':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['is_resolved'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'CSAT':
        agg_df = plot_df.groupby('Group').apply(lambda x: ((x['csat_score'] >= 4).sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Takeover Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['human_takeover'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'Fallback Rate':
        agg_df = plot_df.groupby('Group').apply(lambda x: (x['is_fallback'].sum() / len(x)) * 100).reset_index(name='Val')
    elif y_axis == 'AHT (Mins)':
        agg_df = plot_df.groupby('Group')['average_handling_time'].mean().reset_index(name='Val')
        agg_df['Val'] /= 60
    elif y_axis == 'Volume':
        agg_df = plot_df.groupby('Group').size().reset_index(name='Val')
        
    if x_axis == 'Date':
        # Sort by date
        agg_df = agg_df.sort_values('Group')
        fig = px.line(agg_df, x='Group', y='Val', title=f"{y_axis} over {x_axis}", color_discrete_sequence=[FH_LIGHT])
    elif x_axis == 'Hour of Day':
        agg_df = agg_df.sort_values('Group')
        fig = px.line(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT], markers=True)
    elif x_axis == 'Day of Week':
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        agg_df['Group'] = pd.Categorical(agg_df['Group'], categories=days, ordered=True)
        agg_df = agg_df.sort_values('Group')
        fig = px.bar(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT])
    else:
        # Intent
        agg_df = agg_df.sort_values(by='Val', ascending=False).head(15)
        fig = px.bar(agg_df, x='Group', y='Val', title=f"{y_axis} by {x_axis}", color_discrete_sequence=[FH_LIGHT])
        fig.update_layout(xaxis={'categoryorder':'total descending'})

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=x_axis), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", title=y_axis))
    return fig

if __name__ == '__main__':
    app.run(debug=False, port=8050)
