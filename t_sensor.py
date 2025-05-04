from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
import struct
import threading

def prepare_initial_hr():
    """Holding registerları doğru şekilde başlatın."""
    hr = [0] * 100  # 100 register (0-99), hepsi 0 ile başlar

    # Adres 0-1: 1.23 (float)
    packed = struct.pack('>f', 1.23)
    reg0, reg1 = struct.unpack('>HH', packed)
    hr[0] = reg0
    hr[1] = reg1

    # Adres 12-13: 4.56 (float)
    packed = struct.pack('>f', 4.56)
    reg12, reg13 = struct.unpack('>HH', packed)
    hr[12] = reg12
    hr[13] = reg13

    return hr

def run_server(port, hr_data):
    """Modbus sunucusunu yeni sürüm kurallarıyla başlatın."""
    hr_block = ModbusSequentialDataBlock(0, hr_data)
    store = ModbusSlaveContext(hr=hr_block)  # zero_mode parametresi YOK
    context = ModbusServerContext(slaves=store, single=True)
    print(f"Port {port} üzerinde Modbus sunucusu başlatılıyor...")
    StartTcpServer(context=context, address=("localhost", port))

if __name__ == "__main__":
    hr_data = prepare_initial_hr()

    server1 = threading.Thread(target=run_server, args=(5020, hr_data), daemon=True)
    server1.start()

    server2 = threading.Thread(target=run_server, args=(5021, hr_data), daemon=True)
    server2.start()

    try:
        while True: pass
    except KeyboardInterrupt:
        print("Sunucular durduruluyor...")