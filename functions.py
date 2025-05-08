import  json
import os
import socket


def save_sensors_to_file(sensors):
    with open('sensors.json', 'w') as f:
        json.dump(sensors, f)


def load_sensors_from_file():
    if os.path.exists('sensors.json'):
        with open('sensors.json', 'r') as f:
            return json.load(f)
    return []

def check_connection(ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2)
            s.connect((ip, int(port)))
        return True
    except:
        return False