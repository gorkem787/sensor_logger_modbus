import sqlite3
from datetime import timedelta, datetime
import threading
import dash
import pandas as pd
import plotly.graph_objs as go
from dash import dash_table
from dash import dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from sensor_class import sensor_list
dash.register_page(__name__, path='/')


layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Grafikler", className="text-center my-4"), width=12)
    ]),

    # Kontrol Paneli
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Tarih & Saat Seçimleri
                dbc.Col([
                    dbc.Row([
                        # Başlangıç Zamanı
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

                        # Bitiş Zamanı
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
                ], md=5, className="me-3"),

                # Kontrol Paneli
                dbc.Col([
                    dbc.Stack([
                        # Interval Kontrolü
                        html.Div([
                            html.Label("Okuma Aralığı (saniye)", className="form-label"),
                            dbc.InputGroup([
                                dbc.Input(
                                    id='read-interval-input',
                                    type='number',
                                    className="numeric-input"
                                ),
                                dbc.Button("Güncelle",
                                           id='update-interval',
                                           color="primary",
                                           className="px-3"
                                           )
                            ])
                        ]),

                        # Mod Seçimi
                        html.Div([
                            html.Label("Çalışma Modu", className="form-label mb-2"),
                            dbc.RadioItems(
                                id='live-mode',
                                options=[
                                    {'label': ' Canlı Mod', 'value': 'live'},
                                    {'label': ' Tarih Aralığı', 'value': 'stored'}
                                ],
                                value='live',
                                inline=True,
                                className="radio-group"
                            )
                        ])
                    ], gap=3)
                ], md=4)
            ], align="center"),
            dbc.Row([
                html.Div(id='read-interval-output-container')
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
    ]),

    # Grafikler
    dbc.Row([
        dbc.Col(dcc.Graph(id='mV-graph'), className="mb-4"),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='chlorine-graph'), className="mb-4"),
    ]),

    dbc.Row([
        dbc.Col(dcc.Graph(id='average_mV-graph'), className="mb-4"),
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
                            {'name': 'Average_mV', 'id': 'average_mV'},
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
    dcc.Store(id='read-interval-n', storage_type='local'),
    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,  # 1 second
        n_intervals=0
    ),
    dcc.Interval(
        id='read-interval-n',
        interval=500,
        n_intervals=0
    ),
    dcc.Download(id="download-data")
])],
    )],fluid=True ,className="py-4")

from datetime import datetime


@callback(
    [Output('mV-graph', 'figure'),
     Output('chlorine-graph', 'figure'),
     Output('average_mV-graph', 'figure'),
     Output('chlorine-average-graph', 'figure'),
     Output('sensor-table', 'data'),
     Output('interval-component', 'disabled')],
    [Input('interval-component', 'n_intervals'),
     Input('live-mode', 'value'),
     Input('start-date', 'date'),
     Input('start-time', 'value'),
     Input('end-date', 'date'),
     Input('end-time', 'value'),
     Input('sensor-selector', 'value')],
    [State('interval-component', 'disabled')]
)
def update_all(n, live_mode, start_date, start_time, end_date, end_time, active_sensors, is_disabled):
    try:
        # Tarih formatını düzeltme
        start_date = start_date.split('T')[0] if start_date else None
        end_date = end_date.split('T')[0] if end_date else None

        # Varsayılan saat ayarları
        start_time = start_time or "00:00"
        end_time = end_time or "23:59"

        # Datetime nesneleri oluşturma
        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

        # Veritabanı sorgusu
        with sqlite3.connect('sensor_data.db') as conn:
            if not active_sensors:
                df = pd.DataFrame(columns=['timestamp', 'sensor_id', 'mV', 'chlorine', 'average_mV', 'average_chlorine'])
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
                params = active_sensors + [start_datetime, end_datetime]
                df = pd.read_sql(query, conn, params=params)

        # Grafikleri oluşturma
        figures = []
        for col, title in zip(['mV', 'chlorine', 'average_mV', "average_chlorine"],
                              ['mV', 'Chlorine', 'Moving Average', 'Chlorine Average']):
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

    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
        return [go.Figure()] * 4, [], True


@callback(
    Output("download-data", "data"),
    [Input("btn-csv", "n_clicks"),
     Input("btn-excel", "n_clicks"),
     Input('start-date', 'date'),
     Input('start-time', 'value'),
     Input('end-date', 'date'),
     Input('end-time', 'value')],
    prevent_initial_call=True
)
def download_data(btn_csv, btn_excel, start_date, start_time, end_date, end_time):
    try:
        # Tetikleyici kontrolü
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Tarih ve saatleri birleştirme
        start_date = start_date.split('T')[0] if start_date else datetime.now().strftime('%Y-%m-%d')
        end_date = end_date.split('T')[0] if end_date else datetime.now().strftime('%Y-%m-%d')
        start_time = start_time or "00:00"
        end_time = end_time or "23:59"

        start_datetime = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

        # Veritabanı sorgusu
        with sqlite3.connect('sensor_data.db') as conn:
            df = pd.read_sql('''
                SELECT * FROM sensor_data
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            ''', conn, params=(start_datetime, end_datetime))

        # Dosya formatına göre indirme
        if 'btn-csv' in ctx.triggered[0]['prop_id']:
            return dcc.send_data_frame(df.to_csv, "sensor_data.csv", index=False)
        elif 'btn-excel' in ctx.triggered[0]['prop_id']:
            return dcc.send_data_frame(df.to_excel, "sensor_data.xlsx", index=False)

    except Exception as e:
        print(f"İndirme hatası: {str(e)}")
        return dash.no_update

@callback(
    [Output('read-interval-output-container', 'children'),
     Output('read-interval-n', 'interval')],
    [Input('read-interval-input', 'value'),
     Input('update-interval', 'n_clicks')],
    prevent_initial_call=True
)
def update_interval_settings(interval_value,n_clicks):
    """Update interval display and actual interval timing"""
    ctx = dash.callback_context
    if 'update-interval' in ctx.triggered[0]['prop_id']:
        interval_ms = int(interval_value)
        status_text = f"Veri okuma aralığı: {interval_value} ms"
        return status_text, interval_ms
    else:
        return dash.no_update

@callback([Input('read-interval-n', 'n_intervals')],
    [State('read-interval-n', 'interval'),
     State('sensor-selector', 'value')]
)
def collect_data(n_interval, n, active_sensors):
    if n is None or n == 0:
        return dash.no_update
    print("trig",sensor_list,n_interval)
    # Collect data only from active sensors
    try:
        for sensor in sensor_list:
            sensor.generate_sensor_data()
    except Exception as e:
        print(e)
