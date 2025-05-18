import json

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State

from functions import load_sensors_from_file, save_sensors_to_file, check_connection
from sensor_class import Sensor, sensor_list, ReferanceSensor

dash.register_page(__name__)


# Layout'u fonksiyon olarak tanımla (HER SAYFA YÜKLENİŞİNDE TAZELENSİN)
def layout():
    return dbc.Container([
        html.H1("Sensör Yönetim Paneli", className="mb-4"),
        dcc.Store(id='sensor-store', data=load_sensors_from_file()),
        dcc.Location(id='url', refresh=True),

        # Sensör Ekleme Formu
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(dbc.Input(id="ip-input", placeholder="IP Adresi", type="text")),
                    dbc.Col(dbc.Input(id="port-input", placeholder="Port", type="text")),
                    dbc.Col(dbc.Input(id="id-input", placeholder="Sensör ID", type="text")),
                    dbc.Col( dbc.Select(
                        id='sensor-type',
                        options=[{'label': "Sensor", 'value': "Sensor"},
                                 {'label': "Referance", 'value': "ReferanceSensor"}
                                 ],
                        value='1',
                        className="me-2 mb-2"
                    ),),
                    dbc.Col(dbc.Button("Sensör Ekle", id="add-sensor-btn", color="primary"))
                ])
            ])
        ], className="mb-4"),

        # Sensör Listesi
        dbc.Row([
            dbc.Col([
                html.H4("Aktif Sensörler"),
                html.Div(id="sensor-list", children=show_sensors())  # show_sensors() her yüklemede çağrılacak
            ], width=6)
        ])
    ])


# Sensörleri gösteren fonksiyon
def show_sensors():
    sensors = load_sensors_from_file()  # DOSYADAN HER SEFERİNDE TAZE OKU
    return [
        dbc.Card(
            dbc.CardBody([
                html.H5(f"Sensör ID: {s['id']}"),
                html.P(f"IP: {s['ip']}:{s['port']}"),
                html.P(f"Durum: {s['status']}",
                       className="text-success" if s['status'] == "aktif" else "text-danger"),
                dbc.Button("Sil", id={"type": "delete-btn", "index": s['id']}, color="danger")
            ]),
            className="mb-2"
        ) for s in sensors
    ]


@callback(
    [Output("sensor-store", "data", allow_duplicate=True),
     Output("sensor-list", "children")],
    [Input("add-sensor-btn", "n_clicks"),
     Input({"type": "delete-btn", "index": dash.ALL}, "n_clicks")],
    [State("ip-input", "value"),
     State("port-input", "value"),
     State("id-input", "value"),
     State("sensor-type", "value")],
    prevent_initial_call=True
)
def handle_sensor_actions(add_clicks, delete_clicks, ip, port, sensor_id, sensor_type):
    ctx = dash.callback_context
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]

    # HER İŞLEMDE DOSYADAN TAZE OKU
    sensors = load_sensors_from_file()

    if trigger == "add-sensor-btn":
        if not all([ip, port, sensor_id]):
            return dash.no_update, html.Div("Lütfen tüm alanları doldurun!", className="text-danger")

        if any(s["id"] == sensor_id for s in sensors):
            return dash.no_update, html.Div("Bu ID ile zaten bir sensör var!", className="text-danger")

        # Bağlantı kontrolü yap
        is_active = check_connection(ip, port)
        new_sensor = {
            "id": sensor_id,
            "ip": ip,
            "port": port,
            "sensor-type": sensor_type,
            "status": "aktif" if is_active else "pasif"
        }
        sensors.append(new_sensor)
        if sensor_type == "Referance":
            sensor_list.append(ReferanceSensor(new_sensor["id"], new_sensor["ip"], new_sensor["port"]))
        else:
            sensor_list.append(Sensor(new_sensor["id"], new_sensor["ip"], new_sensor["port"]))
        save_sensors_to_file(sensors)

    elif "delete-btn" in trigger:
        deleted_id = json.loads(trigger).get("index")
        print([s for s in sensor_list if s.sensor_id == deleted_id])
        sensor_list.remove([s for s in sensor_list if s.sensor_id == deleted_id][0])
        sensors = [s for s in sensors if s["id"] != deleted_id]
        save_sensors_to_file(sensors)

    # Listeyi yeniden oluştur
    return sensors, show_sensors()


# Uygulama başlangıcında sensörleri yükle
def initialize_connections():
    sensors = load_sensors_from_file()
    for s in sensors:
        if not any(sensor.sensor_id == s["id"] for sensor in sensor_list):
            if s["sensor-type"] == "Referance":
                new_sensor = ReferanceSensor(s["id"], s["ip"], s["port"])
                new_sensor.status = s["status"]
                sensor_list.append(new_sensor)
            else:
                new_sensor = Sensor(s["id"], s["ip"], s["port"])
                new_sensor.status = s["status"]
                sensor_list.append(new_sensor)

initialize_connections()