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
        # SQLite stores booleans as 0/1 integers. Convert to bool to prevent KeyError during masking.
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG, dbc.icons.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "OTA Intelligence Dashboard"
server = app.server

# Metrics Metadata for Tooltips
metrics_info = {
    "Volume": "Total number of chatbot conversations in the selected period.\nBenchmark: Growing Trend",
    "Handling": "How long a chatbot conversation takes on average.\nBenchmark: 2-5 min",
    "Takeover": "Shows how often a chatbot has to hand a conversation over to a human agent.\nBenchmark: < 25%",
    "Fallback": "How often the chatbot was unable to understand an enquiry and responded with a generic error.\nBenchmark: < 10%",
    "Conversion": "How often the chatbot triggers a desired action (e.g. demo booking, purchase).\nBenchmark: 5-15%",
    "Return Users": "How many users voluntarily use the chatbot a second time or more.\nBenchmark: > 30%"
}

app.layout = html.Div([
    # Sidebar
    html.Div([
        html.H2("OTA DASHBOARD", className="cyber-title", style={"fontSize": "2.2rem", "textAlign": "center"}),
        html.Hr(style={"borderColor": "rgba(35, 173, 224, 0.2)", "marginBottom": "2rem"}),
        
        html.P("Date Range", className="metric-title"),
        dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed=df['timestamp'].min().date(),
            max_date_allowed=df['timestamp'].max().date(),
            start_date=df['timestamp'].min().date(),
            end_date=df['timestamp'].max().date(),
        ),
        
        html.P("Filter by Intent", className="metric-title", style={"marginTop": "2rem"}),
        dcc.Dropdown(
            id='intent-dropdown',
            options=[{'label': i, 'value': i} for i in df['intent'].dropna().unique()],
            multi=True,
            placeholder="All Intents",
            className="custom-dropdown"
        ),
        
        html.Div([
            html.P("SYSTEM STATUS", className="metric-title"),
            html.Div("● ONLINE", style={"color": FH_GREEN, "fontWeight": "bold", "letterSpacing": "2px", "fontSize": "1.2rem"})
        ], style={"position": "absolute", "bottom": "40px"})
    ], id="sidebar", className="sidebar"),
    
    # Main Content
    html.Div([
        html.Button([html.I(className="bi bi-list"), " MENU"], id="btn-sidebar", className="menu-toggle"),
        html.H1("INTELLIGENCE DASHBOARD", className="cyber-title"),
        html.P("Real-time telemetry and advanced KPI modeling.", style={"color": "#8b949e", "fontSize": "1.1rem", "marginBottom": "2rem"}),
        
        # Top Row: Gauges
        dbc.Row([
            dbc.Col(html.Div(dcc.Graph(id='gauge-automation', config={'displayModeBar': False}), className="glass-card", style={"padding": "0"}), width=3),
            dbc.Col(html.Div(dcc.Graph(id='gauge-fcr', config={'displayModeBar': False}), className="glass-card", style={"padding": "0"}), width=3),
            dbc.Col(html.Div(dcc.Graph(id='gauge-csat', config={'displayModeBar': False}), className="glass-card", style={"padding": "0"}), width=3),
            dbc.Col(html.Div(dcc.Graph(id='gauge-deflection', config={'displayModeBar': False}), className="glass-card", style={"padding": "0"}), width=3),
        ], style={"marginBottom": "1.5rem"}),
        
        # Middle Row: Mini Metric Cards
        dbc.Row(id='mini-metrics-row', style={"marginBottom": "1.5rem"}),
        
        # Bottom Row: Large Visualizations
        dbc.Row([
            dbc.Col(html.Div([
                html.H4("Temporal Volume Dynamics", className="metric-title"),
                dcc.Graph(id='chart-timeline', config={'displayModeBar': False})
            ], className="glass-card"), width=7),
            
            dbc.Col(html.Div([
                html.H4("Handling Latency Map", className="metric-title"),
                dcc.Graph(id='chart-intent-aht', config={'displayModeBar': False})
            ], className="glass-card"), width=5)
        ], style={"marginBottom": "2rem"}),
        
        # Slice and Dice Custom Vis
        html.Div([
            html.H3("🔎 Custom Visualizations", style={"color": "white", "textAlign": "center"}),
            html.P("Select any two metrics to dynamically generate a chart based on their data types.", style={"color": "#8b949e", "textAlign": "center", "marginBottom": "1.5rem"}),
            dbc.Row([
                dbc.Col([
                    html.P("Select X-Axis", className="metric-title"),
                    dcc.Dropdown(id='custom-x', options=[{'label': c, 'value': c} for c in df.columns], value='intent', className="custom-dropdown")
                ], width=6),
                dbc.Col([
                    html.P("Select Y-Axis", className="metric-title"),
                    dcc.Dropdown(id='custom-y', options=[{'label': c, 'value': c} for c in df.columns], value='average_handling_time', className="custom-dropdown")
                ], width=6)
            ]),
            dcc.Graph(id='custom-chart', style={"marginTop": "1rem"})
        ], className="glass-card", style={"marginBottom": "2rem"}),
        
        # Anomaly Log
        html.Div([
            html.H3("🚨 Critical Anomaly Log", style={"color": "white", "textAlign": "center"}),
            html.P("Recent conversations requiring human takeover or resulting in a fallback.", style={"color": "#8b949e", "textAlign": "center", "marginBottom": "1.5rem"}),
            html.Div(id='anomaly-table-container')
        ], className="glass-card")
        
    ], id="content", className="content")
])

@app.callback(
    [Output("sidebar", "className"), Output("content", "className")],
    [Input("btn-sidebar", "n_clicks")],
    [State("sidebar", "className")]
)
def toggle_sidebar(n, classname):
    if n and "sidebar-collapsed" not in classname:
        return "sidebar sidebar-collapsed", "content content-expanded"
    return "sidebar", "content"

@app.callback(
    [Output('gauge-automation', 'figure'),
     Output('gauge-fcr', 'figure'),
     Output('gauge-csat', 'figure'),
     Output('gauge-deflection', 'figure'),
     Output('mini-metrics-row', 'children'),
     Output('chart-timeline', 'figure'),
     Output('chart-intent-aht', 'figure'),
     Output('anomaly-table-container', 'children')],
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
        return [go.Figure()] * 4 + [[]] + [go.Figure()] * 2 + [html.P("No data available.")]
        
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
    
    def create_gauge(value, title, color):
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = value,
            number = {'suffix': "%", 'font': {'color': 'white', 'size': 36, 'family': 'Inter'}},
            title = {'text': title, 'font': {'color': '#8b949e', 'size': 14, 'family': 'Inter'}},
            gauge = {
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "rgba(255,255,255,0.1)", 'visible': False},
                'bar': {'color': color, 'thickness': 0.75},
                'bgcolor': "rgba(255,255,255,0.05)",
                'borderwidth': 0,
                'shape': 'angular'
            }
        ))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=30, b=10, l=10, r=10), height=200)
        return fig
        
    g1 = create_gauge(automation_rate, "AUTOMATION", FH_LIGHT)
    g2 = create_gauge(fcr, "RESOLUTION (FCR)", FH_LIGHT)
    g3 = create_gauge(csat, "CSAT POSITIVE", FH_GREEN)
    g4 = create_gauge(deflection_rate, "DEFLECTION", FH_GREEN)
    
    def mini_card(key, value, color, icon):
        return dbc.Col(html.Div([
            html.Div([
                html.Span(f"{icon} {key}", className="metric-title", style={"marginBottom": "5px"}),
                html.I(className="bi bi-info-circle ms-2", id=f"tooltip-{key.replace(' ', '-')}", style={"color": "#8b949e", "cursor": "help"})
            ], style={"display": "flex", "justifyContent": "center", "alignItems": "center"}),
            dbc.Tooltip(metrics_info[key], target=f"tooltip-{key.replace(' ', '-')}", placement="top", style={"whiteSpace": "pre-line"}),
            html.Div(value, className="metric-value", style={"color": color, "fontSize": "2rem"})
        ], className="glass-card", style={"padding": "1rem", "textAlign": "center"}), width=2)
        
    mini_row = [
        mini_card("Volume", f"{total:,}", "#ffffff", "📊"),
        mini_card("Handling", f"{aht_mins:.1f}m", FH_LIGHT, "⏱️"),
        mini_card("Takeover", f"{takeover_rate:.1f}%", "#E74C3C", "🧑‍💻"),
        mini_card("Fallback", f"{fallback_rate:.1f}%", "#E74C3C", "⚠️"),
        mini_card("Conversion", f"{conv_rate:.1f}%", "#f59e0b", "🛒"),
        mini_card("Return Users", f"{ret_rate:.1f}%", FH_LIGHT, "🔄")
    ]
    
    daily = dff.groupby(dff['timestamp'].dt.date).agg(Vol=('timestamp', 'count'), Takeovers=('human_takeover', 'sum')).reset_index()
    fig_time = go.Figure()
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Vol'], mode='lines', name='Volume', line=dict(color=FH_LIGHT, width=3), fill='tozeroy', fillcolor=f'rgba(35, 173, 224, 0.1)'))
    fig_time.add_trace(go.Scatter(x=daily['timestamp'], y=daily['Takeovers'], mode='lines', name='Takeovers', line=dict(color='#E74C3C', width=3)))
    fig_time.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showline=False, title=""), margin=dict(t=20, b=20, l=0, r=0), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=350)
    
    intent_aht = dff.groupby('intent')['average_handling_time'].mean().reset_index()
    intent_aht['average_handling_time'] /= 60
    intent_aht = intent_aht.sort_values(by='average_handling_time', ascending=True).tail(10)
    fig_aht = px.bar(intent_aht, x='average_handling_time', y='intent', orientation='h', color_discrete_sequence=[FH_LIGHT])
    fig_aht.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#8b949e", family="Inter"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)", title="Avg Minutes"), yaxis=dict(title=""), margin=dict(t=10, b=10, l=150, r=0), height=350)
    
    anomaly_df = dff[dff['human_takeover'] | dff['is_fallback']].copy()
    anomaly_df = anomaly_df.sort_values(by='timestamp', ascending=False).head(8)
    if not anomaly_df.empty:
        display_cols = ['timestamp', 'user_id', 'intent', 'is_fallback', 'human_takeover', 'average_handling_time']
        anomaly_table = dbc.Table.from_dataframe(anomaly_df[display_cols], striped=True, bordered=True, hover=True, style={"backgroundColor": "rgba(15, 42, 85, 0.4)", "color": "white"})
    else:
        anomaly_table = html.P("No anomalies detected in the selected period!", style={"color": FH_GREEN})

    return g1, g2, g3, g4, mini_row, fig_time, fig_aht, anomaly_table

@app.callback(
    Output('custom-chart', 'figure'),
    [Input('custom-x', 'value'), Input('custom-y', 'value'), Input('date-picker', 'start_date'), Input('date-picker', 'end_date'), Input('intent-dropdown', 'value')]
)
def update_custom(x_col, y_col, start_date, end_date, selected_intents):
    if x_col == y_col or not x_col or not y_col:
        return go.Figure().update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        
    mask = (df['timestamp'].dt.date >= pd.to_datetime(start_date).date()) & (df['timestamp'].dt.date <= pd.to_datetime(end_date).date())
    if selected_intents:
        mask = mask & (df['intent'].isin(selected_intents))
    plot_df = df[mask][[x_col, y_col]].copy()
    
    if plot_df.empty:
        return go.Figure()

    x_is_dt = pd.api.types.is_datetime64_any_dtype(plot_df[x_col])
    y_is_num = pd.api.types.is_numeric_dtype(plot_df[y_col])
    x_is_num = pd.api.types.is_numeric_dtype(plot_df[x_col])
    
    plot_x = x_col
    if x_is_dt:
        plot_df['_x_date'] = plot_df[x_col].dt.date
        plot_x = '_x_date'
    plot_y = y_col
    if pd.api.types.is_datetime64_any_dtype(plot_df[y_col]):
        plot_df['_y_date'] = plot_df[y_col].dt.date
        plot_y = '_y_date'

    if x_is_dt and y_is_num:
        viz_df = plot_df.groupby(plot_x)[plot_y].mean().reset_index()
        fig = px.line(viz_df, x=plot_x, y=plot_y, title=f"Average {y_col} over Time", color_discrete_sequence=[FH_LIGHT])
    elif not x_is_num and not x_is_dt and y_is_num:
        viz_df = plot_df.groupby(plot_x)[plot_y].mean().reset_index().sort_values(by=plot_y, ascending=False).head(15)
        fig = px.bar(viz_df, x=plot_x, y=plot_y, title=f"Average {y_col} by {x_col}", color_discrete_sequence=[FH_LIGHT])
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
    elif x_is_num and y_is_num:
        sample_df = plot_df.sample(min(2000, len(plot_df)))
        fig = px.scatter(sample_df, x=plot_x, y=plot_y, title=f"{y_col} vs {x_col}", color_discrete_sequence=[FH_LIGHT], opacity=0.5)
    else:
        viz_df = plot_df.groupby([plot_x, plot_y]).size().reset_index(name='count')
        top_x = viz_df.groupby(plot_x)['count'].sum().nlargest(10).index
        viz_df = viz_df[viz_df[plot_x].isin(top_x)]
        fig = px.bar(viz_df, x=plot_x, y='count', color=plot_y, title=f"Count of {y_col} by {x_col}")

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="white"), xaxis=dict(gridcolor="rgba(255,255,255,0.05)"), yaxis=dict(gridcolor="rgba(255,255,255,0.05)"))
    return fig

if __name__ == '__main__':
    app.run(debug=False, port=8050)
