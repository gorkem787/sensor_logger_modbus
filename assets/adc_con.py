import socket

# Hedef adres ve port
HOST = '10.37.64.22'
PORT = 502

# Gönderilecek hex veri (23 30 31 30 0D)
hex_data = bytes.fromhex('233031300D')

# TCP soket oluştur ve bağlan
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(hex_data)
    response = s.recv(1024)  # Yanıtı al (1024 byte'lık buffer)

# Yanıtı hex formatında göster

    temizlenmis_veri = response.decode('utf-8').strip('> \r\n')  # ">-10.20\r" → "-10.20"
    try:
        sayi = float(temizlenmis_veri)
        print("Dönüştürülen sayı:", sayi)  # -10.20
    except ValueError:
        print("Geçersiz sayı formatı!")
