from dash import dcc, html,dash
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import sqlite3
import numpy as np
from sensor_class import sensor_list
import dash

def run_callbacks(app):
    def calculate_calibration(df):
        try:
            x = df['mV'].values
            y = df['chlorine'].values
            coefficients = np.polyfit(x, y, 1)
            print(coefficients)
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
         Output('interval-component', 'disabled')],
        [Input('interval-component', 'n_intervals'),
         Input('live-mode', 'value'),
         Input('date-picker', 'start_date'),
         Input('date-picker', 'end_date'),
         Input('sensor-selector', 'value')],
        [State('interval-component', 'disabled')]
    )
    def update_all(n, live_mode, start_date, end_date, active_sensors, is_disabled):

        for sensor in sensor_list:
            sensor.generate_sensor_data()

        # Veritabanı sorgusu
        with sqlite3.connect('sensor_data.db') as conn:
            if not active_sensors:
                df = pd.DataFrame(columns=['timestamp', 'sensor_id', 'mV', 'chlorine', 'temp'])
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
        for col, title in zip(['mV', 'chlorine', 'temp'], ['mV', 'Chlorine', 'Temperature']):
            fig = go.Figure()
            for sensor_id in active_sensors:
                df_sensor = df[df['sensor_id'] == sensor_id]
                fig.add_trace(go.Scatter(
                    x=df_sensor['timestamp'],
                    y=df_sensor[col],
                    mode='lines+markers',
                    name=f'Sensor {sensor_id}'
                ))
            fig.update_layout(title=f'{title} Takibi')
            figures.append(fig)

        return (*figures, df.to_dict('records'), live_mode != "live")

    @app.callback(
        [Output('calibration-data-mV', 'data'),
         Output('calibration-data-chlorine', 'data')],
        [Input('btn-add-point', 'n_clicks'),
         Input('calibration-sensor', 'value')],
        [State('input-mV', 'value'),
         State('input-chlorine', 'value')]
    )
    def store_calibration_data(n_clicks, sensor_id, mV, chlorine):
        sensor_id = sensor_id[-1]
        sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
        if not sensor:
            return [], []

        if n_clicks and mV is not None and chlorine is not None:
            sensor.add_calibration_data(float(mV), float(chlorine))

        return sensor.c_mv, sensor.c_chlorine


    # Calibration graph callback (updated)
    @app.callback(
        Output('calibration-graph', 'figure'),
         [Input('calibration-sensor', 'value'),
         Input('btn-calibrate', 'n_clicks')]
    )
    def update_calibration_graph(sensor_id, n_clicks):
        ctx = dash.callback_context
        sensor_id = sensor_id[-1]
        sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
        mV_data, chlorine_data = sensor.calibration_data()

        if not ctx.triggered:
            return dash.no_update

        if 'btn-calibrate' in ctx.triggered[0]['prop_id'] and len(mV_data) >= 2:

            df = pd.DataFrame({'mV': mV_data, 'chlorine': chlorine_data})
            a, b, regression_line = calculate_calibration(df)
            # Update sensor's calibration coefficients
            sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
            if sensor:
                sensor.calibration(a, b)
            try:
                a, b, regression_line = calculate_calibration(df)
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
                    name=f'y = {a:.2f}x + {b:.2f}',
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
    @app.callback(
        [Input("btn-reset-point", "n_clicks"),
         Input('calibration-sensor', 'value')]
    )
    def reset(n_clicks, sensor_id):
        sensor_id = sensor_id[-1]
        sensor = next((s for s in sensor_list if s.sensor_id == sensor_id), None)
        ctx = dash.callback_context
        if "btn-reset-point" in ctx.triggered[0]['prop_id']:
            sensor.reset_calibration()

    @app.callback(
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

