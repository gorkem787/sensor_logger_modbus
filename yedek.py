import sqlite3

def rename_temp_to_average_mv():
    with sqlite3.connect('sensor_data.db') as conn:
        c = conn.cursor()

        # 1. Geçici yeni tablo oluştur (temp yerine average_mV ile)
        c.execute('''CREATE TABLE IF NOT EXISTS sensor_data_new
                    (timestamp DATETIME, sensor_id TEXT, mV REAL, 
                     chlorine REAL, average_mV REAL, average_chlorine REAL)''')

        # 2. Eğer temp sütunu varsa verileri kopyala, yoksa average_mV'yi NULL bırak
        try:
            # Eski tablodan yeniye verileri kopyala (temp -> average_mV)
            c.execute('''INSERT INTO sensor_data_new 
                        (timestamp, sensor_id, mV, chlorine, average_mV, average_chlorine)
                        SELECT timestamp, sensor_id, mV, chlorine, temp, average_chlorine 
                        FROM sensor_data''')
        except sqlite3.OperationalError:
            # temp sütunu yoksa, average_mV'yi NULL olarak bırak
            c.execute('''INSERT INTO sensor_data_new 
                        (timestamp, sensor_id, mV, chlorine, average_mV, average_chlorine)
                        SELECT timestamp, sensor_id, mV, chlorine, NULL, average_chlorine 
                        FROM sensor_data''')

        # 3. Eski tabloyu sil
        c.execute('DROP TABLE sensor_data')

        # 4. Yeni tabloyu orijinal adıyla yeniden adlandır
        c.execute('ALTER TABLE sensor_data_new RENAME TO sensor_data')

        conn.commit()

rename_temp_to_average_mv()