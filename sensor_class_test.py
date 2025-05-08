import random
import sqlite3
from datetime import datetime

from pyModbusTCP.client import ModbusClient


class Sensor:
    def __init__(self, sensor_id):
        self.sensor_id = str(sensor_id)
        self.c_mv = []
        self.c_chlorine =[]

    def read_data(self):
        pass

    def calibration(self,a,b):
        self.a = a
        self.b = b

    def calibration_data(self):
        return self.c_mv, self.c_chlorine

    def add_calibration_data(self,mV,chlorine):
        with sqlite3.connect('sensor_calibration_data.db') as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO sensor_calibration_data (sensor_id, mV, chlorine)
                VALUES (?, ?, ?)
            ''', (self.sensor_id, mV, chlorine))
            conn.commit()

    def generate_sensor_data(self):
        mV = random.uniform(800, 1200)
        chlorine = random.uniform(0, 3)
        temp = random.uniform(10, 20)


        timestamp = datetime.now()
        with sqlite3.connect('sensor_data.db') as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO sensor_data (timestamp, sensor_id, mV, chlorine, temp)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, self.sensor_id, mV, chlorine, temp))
            conn.commit()

    def modbus_tcp(self, ip):
        self.client = ModbusClient(host=ip, port=502, auto_open=True)


sensor1 = Sensor(1)
sensor2 = Sensor(2)
sensor_list = [sensor1, sensor2]

