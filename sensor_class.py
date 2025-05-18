import socket
import sqlite3
from datetime import datetime
from time import sleep

import pandas as pd
from pymodbus import FramerType
from pymodbus.client import ModbusTcpClient


class Sensor:
    def __init__(self, sensor_id, host, port, unit_id=1):
        self.unit_id = unit_id  # Modbus slave unit ID
        self.sensor_id = str(sensor_id)
        self.c_mv = []
        self.c_chlorine = []
        self.host = host
        self.port = port
        self.client = ModbusTcpClient(
            host=host,
            port=port,
            framer= FramerType("rtu")
        )
        self.connect()

    def __str__(self):
        return f"{self.sensor_id, self.host, self.port}"

    def connect(self):
        try:
            a = self.client.connect()
            self.connection = a
            print(self.connection)
            return a
        except Exception as e:
            print(e)
            self.connection = False
            return False


    def read_registers(self):
        DATATYPE = self.client.DATATYPE
        response = self.client.read_input_registers(address=0, count=50, slave=self.unit_id)
        sensor_voltage_cal = self.client.convert_from_registers(response.registers[0:2], data_type=DATATYPE.FLOAT32, word_order='big')
        sensor_voltage_raw = self.client.convert_from_registers(response.registers[12:14], data_type=DATATYPE.FLOAT32, word_order='big')
        #print(response_cal,sensor_voltage_cal)

        return sensor_voltage_raw, sensor_voltage_cal

    def calibration_a_b(self,a,b):
        self.a = a
        self.b = b

    def calibration(self):
        DATATYPE = self.client.DATATYPE
        a_registers = self.client.convert_to_registers(self.a,DATATYPE.FLOAT64, word_order='big')
        b_registers = self.client.convert_to_registers(self.b, DATATYPE.FLOAT64, word_order='big')
        # Write calibration parameters
        self.client.write_registers(address=25, values=a_registers, slave=self.unit_id)
        sleep(0.01)
        self.client.write_registers(address=30, values=b_registers, slave=self.unit_id)
        print("Calibre edildi")

    def generate_sensor_data(self):
        if self.connection:
            try:
                mV, chlorine = self.read_registers()
            except Exception as e:
                print(f"Error reading sensor registers: {e}")
                return  # Exit if we can't read sensor data

            # Get historical data for averaging
            try:
                with sqlite3.connect('sensor_data.db') as conn:
                    # Get historical mV average
                    query = """
                        SELECT mV FROM sensor_data
                        WHERE sensor_id = ?
                        ORDER BY timestamp DESC
                        LIMIT 100
                    """
                    df = pd.read_sql(query, conn, params=(self.sensor_id,))
                    # Calculate average (default to 0 if no history)
                    average_mV = df["mV"].mean() if not df.empty and 'mV' in df.columns else 0
                    average_chlorine = df["chlorine"].mean() if not df.empty and 'chlorine' in df.columns else 0
                    if type(average_chlorine) == list:
                        print(average_chlorine)

                    # Insert new data
                    timestamp = datetime.now()
                    print(timestamp, self.sensor_id, mV, chlorine, average_mV, average_chlorine)
                    c = conn.cursor()
                    c.execute('''
                        INSERT INTO sensor_data (timestamp, sensor_id, mV, chlorine, average_mV, average_chlorine)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (timestamp, self.sensor_id, mV, chlorine, average_mV, average_chlorine))
                    conn.commit()

            except sqlite3.Error as e:
                print(f"Database error: {e}")
            except Exception as e:
                print(f"Unexpected error: {e}")

class ReferanceSensor:
    def __init__(self, sensor_id, host, port):
        self.sensor_id = str(sensor_id)
        self.c_mv = []
        self.c_chlorine = []
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((host, port))
        except Exception as e:
            print(e)

    def read_analog(self):
        # Gönderilecek hex veri (23 30 31 30 0D)
        hex_data = bytes.fromhex('233031300D')
        self.s.sendall(hex_data)
        response = self.s.recv(1024)  # Yanıtı al (1024 byte'lık buffer)
        response = response.decode('utf-8').strip('> \r\n')  # ">-10.20\r" → "-10.20"
        print(response)
        try:
            mA = float(response)
        except ValueError:
            print("Analog Okuma Geçersiz sayı formatı!")

        if 3.9 <= mA <= 20.1:
            Chlorine = ((mA - 4) / 16) * 2
        else:
            print("analog kabloyu kontrol et")
            Chlorine = 0
        return Chlorine

    def generate_sensor_data(self):
        try:
            # Read sensor data
            chlorine = self.read_analog()
        except Exception as e:
            print(f"Error reading sensor registers: {e}")
            return  # Exit if we can't read sensor data

        # Get historical data for averaging
        try:
            with sqlite3.connect('sensor_data.db') as conn:
                # Get historical mV average
                query = """
                    SELECT mV FROM sensor_data
                    WHERE sensor_id = ?
                    ORDER BY timestamp DESC
                    LIMIT 100
                """
                df = pd.read_sql(query, conn, params=(self.sensor_id,))
                average_chlorine = df["chlorine"].mean() if not df.empty and 'chlorine' in df.columns else None
                # Insert new data
                timestamp = datetime.now()
                c = conn.cursor()
                c.execute('''
                    INSERT INTO sensor_data (timestamp, sensor_id, chlorine, average_chlorine)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, self.sensor_id, chlorine, average_chlorine))
                conn.commit()

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

#sensor1 = Sensor(1, host="10.37.64.20" , port=502)
#sensor2 = Sensor(2, host="10.37.64.21" , port=502)
#sensor3 = ReferanceSensor(3, host="10.37.64.22" , port=502)
sensor_list = []