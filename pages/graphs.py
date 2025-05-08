import sqlite3
from datetime import timedelta, datetime

import dash
import pandas as pd
import plotly.graph_objs as go
from dash import dash_table
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from sensor_class import sensor_list
dash.register_page(__name__, path='/')

# Tarih seçici için ortak stil
date_picker_style = {
    'backgroundColor': 'white',
    'border': '1px solid #ced4da',
    'borderRadius': '4px',
    'padding': '8px'
}

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Sensör Analiz Paneli", className="text-center my-4"), width=12)
    ]),

    # Kontrol Paneli
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.DatePickerRange(
                        id='date-picker',
                        min_date_allowed=datetime.now() - timedelta(days=30),
                        max_date_allowed=datetime.now(),
                        start_date=datetime.now() - timedelta(days=1),
                        end_date=datetime.now(),
                        display_format='YYYY-MM-DD HH:mm',
                        style=date_picker_style
                    ),
                ], md=4, className="mb-3"),

                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(
                            id='interval-read',
                            type='number',
                            placeholder='Okuma aralığı (ms)',
                            className="me-2"
                        ),
                        dbc.Button("Güncelle", id='update-interval', color="primary")
                    ])
                ], md=3),

                dbc.Col([
                    dbc.RadioItems(
                        id='live-mode',
                        options=[
                            {'label': ' Canlı Veri', 'value': 'live'},
                            {'label': ' Tarih Aralığı', 'value': 'stored'}
                        ],
                        value='live',
                        inline=True
                    )
                ], md=3)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Checklist(
                        id='sensor-selector',
                        options=[
                            {'label': f' Sensör {i}', 'value': str(i)}
                            for i in range(1, 5)
                        ],
                        value=['1', '2', '3', '4'],
                        inline=True,
                        switch=True,
                        className="mt-3"
                    )
                ], width=12),

                dbc.Col([html.Div(id='read-interval-output-container')])
            ])
        ])
    ], className="shadow-sm mb-4"),

    # Grafikler
    dbc.Row([
        dbc.Col(dcc.Graph(id='mV-graph'), className="mb-4"),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='chlorine-graph'), className="mb-4"),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='temp-graph'), className="mb-4"),
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='chlorine-average-graph'), className="mb-4"),
    ]),
    # Veri Tablosu ve İndirme
    dbc.Card([
        dbc.CardHeader("Ham Veri Tablosu", className="fw-bold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("CSV İndir", id='btn-csv', color="success", className="me-2"),
                        dbc.Button("Excel İndir", id='btn-excel', color="warning")
                    ], className="mb-3")
                ], width=12)
            ]),

            dbc.Row([
                dbc.Col([
                    dash_table.DataTable(
                        id='sensor-table',
                        columns=[
                            {'name': 'Zaman', 'id': 'timestamp'},
                            {'name': 'Sensör', 'id': 'sensor_id'},
                            {'name': 'mV', 'id': 'mV'},
                            {'name': 'Chlorine', 'id': 'chlorine'},
                            {'name': 'Average_mV', 'id': 'temp'},
                            {'name': 'average_chlorine', 'id': 'average_chlorine'}
                        ],
                        style_table={'overflowX': 'auto'},
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        page_size=10,
                        filter_action="native",
                        sort_action="native"
                    )
                ], width=12)
            ])
        ])
    ], className="shadow-sm"),

    # Arkaplan Güncelleme Komponentleri
    dcc.Store(id='interval-store'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # 1 second
        n_intervals=0
    ),
    dcc.Interval(
        id='read-interval',
        interval=500,
        n_intervals=0
    ),
    dcc.Download(id="download-data")
], fluid=True, className="py-4")

@callback(
    [Output('mV-graph', 'figure'),
     Output('chlorine-graph', 'figure'),
     Output('temp-graph', 'figure'),
    Output('chlorine-average-graph', 'figure'),
     Output('sensor-table', 'data'),
     Output('interval-component', 'disabled')],
    [Input('interval-component', 'n_intervals'),
     Input('live-mode', 'value'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),
     Input('sensor-selector', 'value')],
    [State('interval-component', 'disabled')]
)
def update_all(n, live_mode, start_date, end_date, active_sensors, is_disabled):
    with sqlite3.connect('sensor_data.db') as conn:
        if not active_sensors:
            df = pd.DataFrame(columns=['timestamp', 'sensor_id', 'mV', 'chlorine', 'temp', 'average_chlorine'])
        elif live_mode == "live":
            query = f"""
                SELECT * FROM sensor_data
                WHERE sensor_id IN ({','.join(['?'] * len(active_sensors))})
                ORDER BY timestamp DESC
                LIMIT 200
            """
            df = pd.read_sql(query, conn, params=active_sensors)
        else:
            query = f"""
                SELECT * FROM sensor_data
                WHERE sensor_id IN ({','.join(['?'] * len(active_sensors))})
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """
            params = active_sensors + [start_date, end_date]
            df = pd.read_sql(query, conn, params=params)

    # Grafikler
    figures = []
    for col, title in zip(['mV', 'chlorine', 'temp', "average_chlorine"], ['mV', 'Chlorine', 'Moving_Average', 'average_chlorine']):
        fig = go.Figure()
        for sensor_id in active_sensors:
            df_sensor = df[df['sensor_id'] == sensor_id]
            fig.add_trace(go.Scatter(
                x=df_sensor['timestamp'],
                y=df_sensor[col],
                mode='lines+markers',
                name=f'Sensor {sensor_id}'
            ))
        fig.update_layout(title=f'{title} Graph')
        figures.append(fig)

    return (*figures, df.to_dict('records'), live_mode != "live")



@callback(
    Output("download-data", "data"),
    [Input("btn-csv", "n_clicks"),
     Input("btn-excel", "n_clicks"),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date'),],
    prevent_initial_call=True
)
def download_data(btn_csv, btn_excel,start_date, end_date):
    ctx = dash.callback_context
    with sqlite3.connect('sensor_data.db') as conn:
        df = pd.read_sql('''
                            SELECT * FROM sensor_data
                            WHERE timestamp BETWEEN ? AND ?
                            ORDER BY timestamp DESC''', conn, params=(start_date, end_date))

    if 'btn-csv' in ctx.triggered[0]['prop_id']:
        return dcc.send_data_frame(df.to_csv, "sensor_data.csv")
    elif 'btn-excel' in ctx.triggered[0]['prop_id']:
        return dcc.send_data_frame(df.to_excel, "sensor_data.xlsx", index=False)

@callback(
    [Output('read-interval-output-container', 'children'),
     Output('read-interval', 'interval')],
    [Input('interval-read', 'value')],
    prevent_initial_call=True
)
def update_interval_settings(interval_value):
    """Update interval display and actual interval timing"""
    # Convert slider value (seconds) to milliseconds for Interval component
    interval_ms = int(interval_value)
    status_text = f"Veri okuma aralığı: {interval_value} ms"
    return status_text, interval_ms

@callback([Input('read-interval', 'n_intervals')],
    [State('read-interval', 'interval'),
     State('sensor-selector', 'value')]
)
def collect_data(n_interval, n, active_sensors):
    if n is None or n == 0:
        return dash.no_update
    print("trig",sensor_list)
    # Collect data only from active sensors
    for sensor in sensor_list:
        sensor.generate_sensor_data()
