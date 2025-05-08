import dash
import pandas as pd
import plotly.graph_objs as go
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
from scipy import stats
import dash_bootstrap_components as dbc
from sensor_class import sensor_list
import sqlite3
import json
dash.register_page(__name__)

layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Sensör Kalibrasyon", className="text-center my-4"), width=12)
    ]),

    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Kalibrasyon Kontrolleri", className="fw-bold"),
                        dbc.CardBody([
                            dbc.Stack([
                                dbc.Select(
                                    id='calibration-sensor',
                                    options=[{'label': f'Sensör {i}', 'value': str(i)} for i in range(1, 5)],
                                    value='1',
                                    className="me-2 mb-2"
                                ),
                                dbc.Input(
                                    id='input-mV',
                                    placeholder='mV Değeri',
                                    className="me-2 mb-2"
                                ),
                                dbc.Input(
                                    id='input-chlorine',
                                    placeholder='Klor Değeri (ppm)',
                                    className="me-2 mb-2"
                                ),
                            ], direction="horizontal", className="flex-wrap"),

                            dbc.ButtonGroup([
                                dbc.Button(
                                    "Nokta Ekle",
                                    id='btn-add-point',
                                    color="primary",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Kalibrasyonu Sıfırla",
                                    id='btn-reset-point',
                                    color="danger",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Hesapla",
                                    id='btn-calibrate',
                                    color="success",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Gönder",
                                    id='btn-send',
                                    color="info"
                                )
                            ], className="mt-3")
                        ])
                    ], className="shadow-sm")
                ], md=4),

                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Kalibrasyon Durumu", className="fw-bold"),
                        dbc.CardBody([
                            html.Div(id='calibration-status', className="text-center"),
                            dcc.Graph(
                                id='calibration-graph',
                                config={'displayModeBar': False},
                                className="mt-3"
                            )
                        ])
                    ], className="shadow-sm")
                ], md=8)
            ], className="g-4"),
            dbc.Row([
                dbc.Card([
                dbc.CardHeader(["Seçilen Nokta"]),
                dbc.CardBody([
                         html.Div(id="selected-data"),
                    dbc.Button(
                        "Sil",
                        id='btn-selected-data-remove',
                        color="danger",
                        className="me-2"
                    ),
                ])
            ])],className="flex-wrap"),
        ])
    ]),

    dcc.Store(id='calibration-data-mV'),
    dcc.Store(id='calibration-data-chlorine')
], fluid=True, className="py-4")

def calculate_calibration(df):
    try:
        x = df['mV'].values
        y = df['chlorine'].values
        coefficients = stats.linregress(x, y)

        a = coefficients.slope
        b = coefficients.intercept
        r = coefficients.rvalue

        regression_line = a * x + b
        print(a, b, r, regression_line)
        return a, b, r, regression_line
    except:
        return 0, 0, 0, []

@callback(
    [Output('calibration-data-mV', 'data'),
     Output('calibration-data-chlorine', 'data')],
    [Input('btn-add-point', 'n_clicks'),
     Input('calibration-sensor', 'value')],
    [State('input-mV', 'value'),
     State('input-chlorine', 'value')]
)
def store_calibration_data(n_clicks, sensor_id, mV, chlorine):
    sensor_id = sensor_id[-1]

    if n_clicks and mV is not None and chlorine is not None:
        with sqlite3.connect('sensor_calibration_data.db') as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO calibration_data (sensor_id, mV, chlorine)
                VALUES (?, ?, ?)
            ''', (sensor_id, mV, chlorine))
            conn.commit()

    return mV, chlorine


# Calibration graph callback (updated)
@callback(
    Output('calibration-graph', 'figure'),
     [Input('calibration-sensor', 'value'),
     Input('btn-calibrate', 'n_clicks')]
)
def update_calibration_graph(sensor_id, n_clicks):
    ctx = dash.callback_context
    sensor_id = sensor_id[-1]
    sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
    def calibration_data(sensor_id):
        c_mv = []
        c_chlorine = []

        with sqlite3.connect('sensor_calibration_data.db') as conn:
            c = conn.cursor()
            # Tüm kalibrasyon verilerini al
            c.execute('''
                SELECT mV, chlorine FROM calibration_data
                WHERE sensor_id = ?
            ''', (sensor_id))
            results = c.fetchall()

        if results:
            c_mv = [row[0] for row in results]
            c_chlorine = [row[1] for row in results]

        return c_mv, c_chlorine
    mV_data, chlorine_data = calibration_data(sensor_id)
    if not ctx.triggered:
        return dash.no_update

    if 'btn-calibrate' in ctx.triggered[0]['prop_id'] and len(mV_data) >= 3:

        df = pd.DataFrame({'mV': mV_data, 'chlorine': chlorine_data})
        a, b, r,regression_line = calculate_calibration(df)
        sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
        if sensor is not None:
            sensor.calibration_a_b(a,b)

        try:
            a, b, r, regression_line = calculate_calibration(df)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['mV'],
                y=df['chlorine'],
                mode='markers',
                name='Calibration Points',
                marker=dict(size=12, color='#FF4C72')
            ))
            fig.add_trace(go.Scatter(
                x=df['mV'],
                y=regression_line,
                mode='lines',
                name=f'y = {a:.4f}x + {b:.4f} R = {r:.4f}',
                line=dict(color='#2D5F8B', dash='dot')
            ))
            fig.update_layout(
                title=f'Sensor {sensor_id} Calibration Curve',
                xaxis_title='mV Reading',
                yaxis_title='Chlorine Concentration (ppm)',
                template='plotly_white',
                height=400,
                margin=dict(l=60, r=40, t=80, b=60)
            )
            return fig
        except Exception as e:
            return go.Figure().update_layout(
                title="Calibration Error",
                annotations=[dict(
                    text=f"Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False
                )]
            )
    return dash.no_update

@callback([Input('btn-send', 'n_clicks'),
               Input('calibration-sensor', 'value')])
def send_calibration(n_clicks, sensor_id):
    sensor_id = sensor_id[-1]
    sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
    ctx = dash.callback_context
    if "btn-send" in ctx.triggered[0]['prop_id']:
        print(sensor)
        sensor.calibration()

@callback(
    [Input("btn-reset-point", "n_clicks"),
     Input('calibration-sensor', 'value')]
)
def reset(n_clicks, sensor_id):
    sensor_id = sensor_id[-1]
    ctx = dash.callback_context
    if "btn-reset-point" in ctx.triggered[0]['prop_id']:
        """Reset sensor calibration to default values in the database"""
        with sqlite3.connect('sensor_calibration_data.db') as conn:
            c = conn.cursor()
            # First clear existing calibration data
            c.execute('''
                DELETE FROM calibration_data
                WHERE sensor_id = ?
            ''', (sensor_id))

@callback(
    Output('selected-data', 'children'),
    Input('calibration-graph', 'clickData'),
    Input('btn-selected-data-remove', 'n_clicks'),)
def display_click_data(clickData,n_clicks):
    clickData = clickData['points'][0]
    print(clickData)
    return f"x = {clickData['x']}, y = {clickData['y']}"
