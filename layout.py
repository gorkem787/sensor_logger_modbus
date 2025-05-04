from dash import dcc, html, dash_table
from datetime import datetime, timedelta


def create_layout(app):
    app.title = "Sensör_Takip"

    return html.Div([
        html.H1("Sensör Veri Takip Sistemi", style={'textAlign': 'center', 'color': '#2c3e50'}),

        # Zaman aralığı seçimi
        html.Div([
            dcc.DatePickerRange(
                id='date-picker',
                min_date_allowed=datetime.now() - timedelta(days=30),
                max_date_allowed=datetime.now(),
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now(),
                display_format='YYYY-MM-DD HH:mm'
            ),

            dcc.RadioItems(
                options=[
                    {'label': ' Canlı Veri', 'value': 'live'},
                    {'label': ' Kayıtlı Veri', 'value': 'stored'}
                ],
                value='live',
                id='live-mode',
                className='RadioItems',
                labelStyle={'display': 'inline-block', 'margin': '10px'}
            )
        ], style={'textAlign': 'center', 'padding': '20px'}),

        html.Div([
            dcc.Slider(
                id='interval-slider',
                min=300,
                max=2000,
                step=100,
                value=500,
                marks={i: f"{i}s" for i in range(200, 2000, 100)}
            ),

            # Interval component
            dcc.Interval(
                id='data-interval',
                interval=500,  # Initial value matches slider
                n_intervals=0
            )
        ], style={'textAlign': 'center'}),

        # Output display
        html.Div(id='read-interval-output-container', style={'width': '80%', 'margin': '0 auto','textAlign': 'center'}),

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
            className='Checklist',
            labelStyle={'margin-right': '15px', 'textAlign': 'center'}
        ),

        # Grafikler
        html.Div([
            html.Div([dcc.Graph(id='mV-graph')], className='six columns'),
            html.Div([dcc.Graph(id='chlorine-graph')], className='six columns'),
            html.Div([dcc.Graph(id='temp-graph')], className='six columns'),

            # Kalibrasyon bölümü
            html.Div([
                html.H3("Sensor Calibration", style={'marginTop': '30px','textAlign': 'center'}),
                dcc.Store(id='calibration-data-mV'),
                dcc.Store(id='calibration-data-chlorine'),
                html.Div([
                    dcc.Dropdown(
                        id='calibration-sensor',
                        options=[{'label': f'Sensor {i}', 'value': str(i)} for i in range(1, 5)],
                        value='1',
                        style={'width': '200px', 'margin': '10px'}
                    ),
                    dcc.Input(
                        id='input-mV',
                        type='number',
                        placeholder='mV Value',
                        style={'margin': '10px', 'width': '120px'}
                    ),
                    dcc.Input(
                        id='input-chlorine',
                        type='number',
                        placeholder='Chlorine Value (ppm)',
                        style={'margin': '10px', 'width': '120px'}
                    ),
                    html.Button(
                        "Add Calibration Point",
                        id='btn-add-point',
                        style={'margin': '10px'}
                    ),
                    html.Button(
                        "Reset Calibration",
                        id='btn-reset-point',
                        style={'margin': '10px'}
                    ),
                    html.Button(
                        "Calculate Calibration",
                        id='btn-calibrate',
                        style={'margin': '10px'}
                    ),

                    html.Button(
                        "Send Calibration",
                        id='btn-send',
                        style={'margin': '10px'}
                    )
                ], style={'display': 'flex', 'justifyContent': 'center', 'flexWrap': 'wrap'}),
                html.Div(id='calibration-status'),
                dcc.Graph(id='calibration-graph')
            ], className='twelve columns', style={'marginTop': '30px'}),
        ], className='row'),

        # Tablo ve indirme butonları
        html.Div([
            html.Div([
                html.Button(
                    "CSV Olarak İndir",
                    id='btn-csv',
                    className='button',
                    style={'marginRight': '10px'}
                ),
                html.Button(
                    "Excel Olarak İndir",
                    id='btn-excel',
                    className='button'
                ),
                dcc.Download(id="download-data")
            ], style={'margin': '20px 0', 'textAlign': 'center'}),

            dash_table.DataTable(
                id='sensor-table',
                columns=[
                    {'name': 'Zaman', 'id': 'timestamp'},
                    {'name': 'Sensör', 'id': 'sensor_id'},
                    {'name': 'mV', 'id': 'mV'},
                    {'name': 'Chlorine', 'id': 'chlorine'},
                    {'name': 'Sıcaklık', 'id': 'temp'}
                ],
                style_table={
                    'overflowX': 'auto',
                    'maxWidth': '100%',
                    'margin': '0 auto'
                },
                style_cell={
                    'textAlign': 'center',
                    'padding': '10px'
                },
                page_size=10,
                filter_action="native",
                sort_action="native"
            )
        ], style={'padding': '20px'}),

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
    ])