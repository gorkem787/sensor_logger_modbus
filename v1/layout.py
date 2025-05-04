from dash import dcc, html, dash_table
from datetime import datetime, timedelta

def create_layout(app):
    app.title = "Sensör_Takip"

    app.layout = (html.Div([
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
                style={'margin': '50px','width': '1000px'}
            ),

            dcc.RadioItems(options=["live","stored"],
                           value='live',
                            id='live-mode',
                           className='RadioItems'),


            dcc.Checklist(
                id='sensor-selector',
                options=[
                    {'label': ' Sensor 1', 'value': '1'},
                    {'label': ' Sensor 2', 'value': '2'},
                    {'label': ' Sensor 3', 'value': '3'},
                    {'label': ' Sensor 4', 'value': '4'},
                ],
                value=['1', '2','3','4'],
                inline=True,
                className='Checklist'
            )
        ], style={'textAlign': 'center'}),


        # Grafikler
        html.Div([
            html.Div([dcc.Graph(id='mV-graph')], className='six columns'),
            html.Div([dcc.Graph(id='chlorine-graph')], className='six columns'),
            html.Div([dcc.Graph(id='temp-graph')], className='six columns'),
            html.Div([
                html.H3("Sensor Calibration", style={'marginTop': '30px'}),
                dcc.Store(id='calibration-data-mV'),  # Add Store component
                dcc.Store(id='calibration-data-chlorine'),  # Add Store component
                html.Div([
                    dcc.Input(id='input-mV', placeholder='mV Value',
                              style={'margin': '10px'}),
                    dcc.Input(id='input-chlorine', placeholder='Chlorine Value (ppm)',
                              style={'margin': '10px'}),
                    html.Button("Add Calibration Point", id='btn-add-point',
                                style={'margin': '10px'}),
                    html.Button("Reset Calibration", id='btn-reset-point',
                                style={'margin': '10px'}),
                    html.Button("Calculate Calibration", id='btn-calibrate',
                                style={'margin': '10px'}),
                    dcc.Dropdown(
                        id='calibration-sensor',
                        options=[{'label': f'Sensor {i}', 'value': str(i)} for i in range(1, 5)],
                        value='1',
                        style={'width': '200px', 'margin': '10px'}
                    ),
                ], style={'display': 'flex', 'justifyContent': 'center'}),
            ], style={'textAlign': 'center', 'padding': '20px'}),

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
    ], style={'backgroundColor': '#f9f9f9'}))