import random
import sqlite3
from datetime import datetime
from pymodbus.client import ModbusTcpClient
import struct
from pymodbus import FramerType
from time import sleep


class Sensor:
    def __init__(self, sensor_id, host, port, unit_id=1):
        self.unit_id = unit_id  # Modbus slave unit ID
        self.sensor_id = str(sensor_id)
        self.c_mv = []
        self.c_chlorine = []
        self.client = ModbusTcpClient(
            host=host,
            port=port,
            framer= FramerType("rtu")
        )

        try:
            self.client.connect()
        except Exception as e:
            print(e)

    def read_registers(self):
        DATATYPE = self.client.DATATYPE
        response_raw = self.client.read_input_registers(address=12, count=2, slave=self.unit_id)
        sensor_voltage_raw = self.client.convert_from_registers(response_raw.registers, data_type=DATATYPE.FLOAT32, word_order='big')
        #print(response_raw,sensor_voltage_raw)
        sleep(0.1)
        response_cal = self.client.read_input_registers(address=0, count=2, slave=self.unit_id)
        sensor_voltage_cal = self.client.convert_from_registers(response_cal.registers, data_type=DATATYPE.FLOAT32, word_order='big')
        #print(response_cal,sensor_voltage_cal)

        return sensor_voltage_raw, sensor_voltage_cal

    def calibration(self, a, b):
        DATATYPE = self.client.DATATYPE
        a_registers = self.client.convert_to_registers(a,DATATYPE.FLOAT64, word_order='big')
        b_registers = self.client.convert_to_registers(b, DATATYPE.FLOAT64, word_order='big')
        # Write calibration parameters
        self.client.write_registers(address=25, values=a_registers, slave=self.unit_id)
        self.client.write_registers(address=30, values=b_registers, slave=self.unit_id)

    def calibration_data(self):
        return self.c_mv, self.c_chlorine

    def add_calibration_data(self, mv, chlorine):
        self.c_mv.append(mv)
        self.c_chlorine.append(chlorine)

    def reset_calibration(self):
        self.c_mv = []
        self.c_chlorine = []

    def generate_sensor_data(self):
        try:
            mV, chlorine = self.read_registers()
        except Exception as e:
            print(e)
        temp = random.uniform(10, 20)

        timestamp = datetime.now()
        with sqlite3.connect('sensor_data.db') as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO sensor_data (timestamp, sensor_id, mV, chlorine, temp)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, self.sensor_id, mV, chlorine, temp))
            conn.commit()


sensor1 = Sensor(1, host="172.10.10.14" , port=502)
sensor2 = Sensor(2, host="172.10.10.15", port=502)
sensor_list = [sensor1,sensor2]