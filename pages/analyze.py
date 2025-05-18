import sqlite3
from datetime import timedelta, datetime
from itertools import combinations

import dash
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import numpy as np

dash.register_page(__name__, path='/analyze')


# Initialize databases
def initialize_database():
    with sqlite3.connect('sensor_data.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                     (timestamp DATETIME, sensor_id TEXT, mV REAL, chlorine REAL, average_mV REAL, average_chlorine REAL)''')
        conn.commit()


def initialize_calibration_database():
    with sqlite3.connect('sensor_calibration_data.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS calibration_data
                     (sensor_id TEXT, mV REAL, chlorine REAL)''')
        conn.commit()


# Layout
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    html.Label("Başlangıç Zamanı", className="form-label"),
                    dcc.DatePickerSingle(
                        id='start-date',
                        max_date_allowed=datetime.now().date(),
                        date=(datetime.now() - timedelta(days=1)).date(),
                        display_format='YYYY-MM-DD',
                        className="mb-2"
                    ),
                    dbc.Input(
                        id='start-time',
                        type='time',
                        value=(datetime.now() - timedelta(days=1)).strftime('%H:%M'),
                        className="time-picker"
                    )
                ], md=6),
                dbc.Col([
                    html.Label("Bitiş Zamanı", className="form-label"),
                    dcc.DatePickerSingle(
                        id='end-date',
                        max_date_allowed=datetime.now().date(),
                        date=datetime.now().date(),
                        display_format='YYYY-MM-DD',
                        className="mb-2"
                    ),
                    dbc.Input(
                        id='end-time',
                        type='time',
                        value=datetime.now().strftime('%H:%M'),
                        className="time-picker"
                    )
                ], md=6)
            ])
        ])
    ]),
    dbc.Tabs([
        dbc.Tab(label="Korelasyon Analizi", tab_id="tab-correlation"),
        dbc.Tab(label="İstatistiksel Analiz", tab_id="tab-statistics"),
        dbc.Tab(label="Zaman Serisi Analizi", tab_id="tab-timeseries"),
    ], id="analyze-tabs", active_tab="tab-correlation"),
    html.Div(id="analyze-tab-content", className="p-4")
], fluid=True)


# Callbacks
@callback(
    Output("analyze-tab-content", "children"),
    Input('start-date', 'date'),
    Input('start-time', 'value'),
    Input('end-date', 'date'),
    Input('end-time', 'value'),
    Input("analyze-tabs", "active_tab")
)
def render_tab_content(start_date, start_time, end_date, end_time, active_tab):
    start_date = start_date.split('T')[0] if start_date else (datetime.now() - timedelta(days=1)).date()
    end_date = end_date.split('T')[0] if end_date else datetime.now().date()

    start_time = start_time or "00:00"
    end_time = end_time or "23:59"

    start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    with sqlite3.connect('sensor_data.db') as conn:
        query = """
            SELECT * 
            FROM sensor_data 
            WHERE timestamp BETWEEN ? AND ? 
            ORDER BY timestamp
        """
        df = pd.read_sql(query, conn, params=(start_datetime, end_datetime))
        df['timestamp'] = pd.to_datetime(df['timestamp'])

    if active_tab == "tab-correlation":
        return correlation_analysis(df)
    elif active_tab == "tab-statistics":
        return statistical_analysis(df)
    elif active_tab == "tab-timeseries":
        return timeseries_analysis(df)
    return html.Div("Lütfen bir sekme seçin")


def correlation_analysis(df):
    if df.empty or len(df['sensor_id'].unique()) < 2:
        return dbc.Alert("Korelasyon analizi için en az iki sensör gereklidir.", color="warning")

    numeric_cols = ['timestamp', 'mV', 'chlorine', 'average_mV', 'average_chlorine']
    sensor_groups = df.groupby('sensor_id')
    sensor_dfs = {sensor_id: group[numeric_cols] for sensor_id, group in sensor_groups}

    corr_data = []
    for (s1, df1), (s2, df2) in combinations(sensor_dfs.items(), 2):
        merged = pd.merge_asof(
            df1.sort_values('timestamp'),
            df2.sort_values('timestamp'),
            on='timestamp',
            direction='nearest',
            tolerance=pd.Timedelta(seconds=10),
            suffixes=(f'_{s1}', f'_{s2}')
        )
        if merged.empty:
            continue

        corr_matrix = merged.corr(numeric_only=True)
        cross_corr = corr_matrix.loc[
            [col for col in corr_matrix.columns if str(s1) in col],
            [col for col in corr_matrix.columns if str(s2) in col]
        ]
        corr_data.append((cross_corr, f'Sensör {s1} vs {s2}', s1, s2))

    if not corr_data:
        return dbc.Alert("Yeterli veri bulunamadı.", color="warning")

    graphs = []
    for idx, (matrix, title, s1, s2) in enumerate(corr_data):
        fig = px.imshow(
            matrix,
            x=matrix.columns,
            y=matrix.index,
            color_continuous_scale='RdBu',
            zmin=-1,
            zmax=1,
            title=title
        )
        fig.update_layout(
            height=500,
            xaxis_title=f"Sensör {s2} Özellikleri",
            yaxis_title=f"Sensör {s1} Özellikleri"
        )
        graphs.append(dbc.Col(dcc.Graph(figure=fig), md=6))

    return dbc.Row(graphs)


def statistical_analysis(df):
    if df.empty:
        return dbc.Alert("Veri bulunamadı.", color="warning")

    numeric_cols = ['mV', 'chlorine', 'average_mV', 'average_chlorine']
    stats = df.groupby('sensor_id')[numeric_cols].describe().stack(0).reset_index()

    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("İstatistiksel Özet"),
                dbc.CardBody(dash.dash_table.DataTable(
                    data=stats.to_dict('records'),
                    columns=[{'name': i, 'id': i} for i in stats.columns],
                    page_size=10
                ))
            ])
        ], md=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Dağılım Grafiği"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='sensor-selector',
                        options=[{'label': i, 'value': i} for i in df['sensor_id'].unique()],
                        value=df['sensor_id'].iloc[0]
                    ),
                    dcc.Dropdown(
                        id='metric-selector',
                        options=[{'label': col, 'value': col} for col in numeric_cols],
                        value=numeric_cols[0]
                    ),
                    dcc.Graph(id='distribution-plot')
                ])
            ])
        ], md=6)
    ])


@callback(
    Output('distribution-plot', 'figure'),
    [Input('sensor-selector', 'value'),
     Input('metric-selector', 'value'),
     Input('start-date', 'date'),
     Input('start-time', 'value'),
     Input('end-date', 'date'),
     Input('end-time', 'value')]
)
def update_distribution_plot(sensor, metric, start_date, start_time, end_date, end_time):
    start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    with sqlite3.connect('sensor_data.db') as conn:
        query = "SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ?"
        df = pd.read_sql(query, conn, params=(start_datetime, end_datetime))

    filtered = df[df['sensor_id'] == sensor]
    fig = px.histogram(filtered, x=metric, marginal='box', title=f"{sensor} - {metric} Dağılımı")
    return fig


def timeseries_analysis(df):
    if df.empty:
        return dbc.Alert("Veri bulunamadı.", color="warning")

    return dbc.Card([
        dbc.CardHeader("Zaman Serisi"),
        dbc.CardBody([
            dcc.Dropdown(
                id='timeseries-metric',
                options=[
                    {'label': 'mV', 'value': 'mV'},
                    {'label': 'Klor', 'value': 'chlorine'}
                ],
                value='mV'
            ),
            dcc.Graph(id='timeseries-plot')
        ])
    ])


@callback(
    Output('timeseries-plot', 'figure'),
    [Input('timeseries-metric', 'value'),
     Input('start-date', 'date'),
     Input('start-time', 'value'),
     Input('end-date', 'date'),
     Input('end-time', 'value')]
)
def update_timeseries(metric, start_date, start_time, end_date, end_time):
    start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    with sqlite3.connect('sensor_data.db') as conn:
        query = "SELECT * FROM sensor_data WHERE timestamp BETWEEN ? AND ?"
        df = pd.read_sql(query, conn, params=(start_datetime, end_datetime))

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    fig = px.line(df, x='timestamp', y=metric, color='sensor_id', title="Zaman Serisi Analizi")
    return fig