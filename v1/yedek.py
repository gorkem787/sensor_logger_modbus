import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
import pandas as pd
import sqlite3
import numpy as np
from sensor_class_test import Sensor

def initialize_database():
    with sqlite3.connect('sensor_data.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                    (timestamp DATETIME, sensor_id TEXT, mV REAL, chlorine REAL, temp REAL)''')
        conn.commit()


initialize_database()

app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Sensör Veri Takip Sistemi", style={'textAlign': 'center', 'color': '#2c3e50'}),

    # Zaman aralığı seçimi
    html.Div([
        dcc.DatePickerRange(
            id='date-picker',
            min_date_allowed=datetime.now() - timedelta(days=30),
            max_date_allowed=datetime.now(),
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now(),
            display_format='YYYY-MM-DD HH:mm',
            style={'margin': '20px'}
        ),
        html.Button('Canlı Mod', id='live-mode-btn', style={'margin': '20px'})
    ], style={'textAlign': 'center'}),

    # Grafikler
    html.Div([
        html.Div([dcc.Graph(id='mV-graph')], className='six columns'),
        html.Div([dcc.Graph(id='chlorine-graph')], className='six columns'),
        html.Div([dcc.Graph(id='temp-graph')], className='six columns'),
        html.Div([dcc.Graph(id='calibration-graph')], className='twelve columns'),
    ], className='row'),

    # Kalibrasyon bilgisi
    html.Div(id='calibration-info', style={
        'padding': '20px',
        'margin': '10px',
        'border': '1px solid #ddd',
        'borderRadius': '5px',
        'backgroundColor': '#f8f9fa'
    }),

    # Kontroller ve Tablo
    html.Div([
        html.Div([
            html.Button("CSV Olarak İndir", id='btn-csv', className='button'),
            html.Button("Excel Olarak İndir", id='btn-excel', className='button'),
            dcc.Download(id="download-data")
        ], style={'margin': '20px 0'}),

        dash_table.DataTable(
            id='sensor-table',
            columns=[
                {'name': 'Zaman', 'id': 'timestamp'},
                {'name': 'Sensör', 'id': 'sensor_id'},
                {'name': 'mV', 'id': 'mV'},
                {'name': 'Chlorine', 'id': 'chlorine'},
                {'name': 'Sıcaklık', 'id': 'temp'}
            ],
            style_table={'overflowX': 'auto'},
            page_size=10
        )
    ], className='row', style={'padding': '20px'}),

    dcc.Interval(
        id='interval-component',
        interval=1 * 1000,
        n_intervals=0,
        disabled=False
    )
], style={'backgroundColor': '#f9f9f9'})


sensor1 = Sensor(1)
sensor2 = Sensor(2)
sensor_list = [sensor1, sensor2]

def calculate_calibration(df):
    try:
        x = df['mV'].values
        y = df['chlorine'].values
        coefficients = np.polyfit(x, y, 1)
        a = coefficients[0]
        b = coefficients[1]
        regression_line = a * x + b
        return a, b, regression_line
    except:
        return 0, 0, []


@app.callback(
    [Output('mV-graph', 'figure'),
     Output('chlorine-graph', 'figure'),
     Output('temp-graph', 'figure'),
     Output('sensor-table', 'data'),
     Output('interval-component', 'disabled'),
     Output('calibration-graph', 'figure'),
     Output('calibration-info', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('live-mode-btn', 'n_clicks'),
     Input('date-picker', 'start_date'),
     Input('date-picker', 'end_date')],
    [State('interval-component', 'disabled')]
)
def update_all(n, btn_clicks, start_date, end_date, is_disabled):
    ctx = dash.callback_context
    live_mode = not is_disabled

    for sensor in sensor_list:
        sensor.generate_sensor_data()

    with sqlite3.connect('sensor_data.db') as conn:
        if live_mode:
            df = pd.read_sql('''
                SELECT * FROM sensor_data
                ORDER BY timestamp DESC
                LIMIT 200
            ''', conn)
        else:
            df = pd.read_sql(f'''
                SELECT * FROM sensor_data
                WHERE timestamp BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY timestamp DESC
            ''', conn)

    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        df = pd.DataFrame(columns=['timestamp', 'sensor_id', 'mV', 'chlorine', 'temp'])

    # Ana grafikler
    figures = []
    for col, title in zip(['mV', 'chlorine', 'temp'], ['mV', 'Chlorine', 'Temperature']):
        fig = go.Figure()
        for sensor in sensor_list:
            df_sensor = df[df['sensor_id'] == sensor.sensor_id]
            fig.add_trace(go.Scatter(
                x=df_sensor['timestamp'],
                y=df_sensor[col],
                mode='lines+markers',
                name=f'Sensor {sensor.sensor_id}',
                line=dict(width=2),
                marker=dict(size=8)
            ))
        fig.update_layout(
            title=f'{title} Takibi',
            xaxis_title='Zaman',
            yaxis_title=title,
            template='plotly_white',
            height=300,
            margin=dict(l=50, r=30, t=50, b=30)
        )
        figures.append(fig)

    # Kalibrasyon grafiği ve hesaplamalar
    calibration_fig = go.Figure()
    a, b, regression_line = calculate_calibration(df)

    for sensor in sensor_list:
        df_sensor = df[df['sensor_id'] == sensor.sensor_id]
        calibration_fig.add_trace(go.Scatter(
            x=df_sensor['mV'],
            y=df_sensor['chlorine'],
            mode='markers',
            name=f'Sensor {sensor.sensor_id}',
            marker=dict(size=8)
        ))

    if len(regression_line) > 0:
        calibration_fig.add_trace(go.Scatter(
            x=df['mV'],
            y=regression_line,
            mode='lines',
            name='Kalibrasyon Eğrisi',
            line=dict(color='red', width=3)
        ))

    calibration_fig.update_layout(
        title='mV-Chlorine Kalibrasyon Eğrisi',
        xaxis_title='mV Değeri',
        yaxis_title='Chlorine Konsantrasyonu',
        template='plotly_white',
        height=500
    )

    calibration_info = html.Div([
        html.H4("Kalibrasyon Parametreleri:"),
        html.P(f"Eğim (a): {a:.6f} ppm/mV"),
        html.P(f"Kesim Noktası (b): {b:.6f} ppm"),
        html.P(f"Denklem: Chlorine = {a:.4f}·mV + {b:.4f}")
    ])

    if ctx.triggered and 'live-mode-btn' in ctx.triggered[0]['prop_id']:
        live_mode = not live_mode

    return figures[0], figures[1], figures[2], df.to_dict('records'), not live_mode, calibration_fig, calibration_info


@app.callback(
    Output("download-data", "data"),
    [Input("btn-csv", "n_clicks"),
     Input("btn-excel", "n_clicks")],
    prevent_initial_call=True
)
def download_data(btn_csv, btn_excel):
    ctx = dash.callback_context
    with sqlite3.connect('sensor_data.db') as conn:
        df = pd.read_sql('SELECT * FROM sensor_data', conn)

    if 'btn-csv' in ctx.triggered[0]['prop_id']:
        return dcc.send_data_frame(df.to_csv, "sensor_data.csv")
    elif 'btn-excel' in ctx.triggered[0]['prop_id']:
        return dcc.send_data_frame(df.to_excel, "sensor_data.xlsx", index=False)



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
