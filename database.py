import sqlite3

def initialize_database():
    with sqlite3.connect('sensor_data.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data
                    (timestamp DATETIME, sensor_id TEXT, mV REAL, chlorine REAL, temp REAL, average_chlorine REAL)''')
        conn.commit()

def initialize_calibration_database():
    with sqlite3.connect('sensor_calibration_data.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS calibration_data
                        (sensor_id TEXT,mV REAL, chlorine REAL)''')
        conn.commit()
