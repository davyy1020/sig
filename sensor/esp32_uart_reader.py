"""
ESP32 Serial UART Receiver for Jetson Nano
===========================================
Menerima telemetry data sensor dari ESP32 via jalur Hardware Serial RX/TX 
(/dev/ttyTHS1) atau USB Serial (/dev/ttyUSB0 / /dev/ttyACM0).
"""

import time
import json
import serial
import serial.tools.list_ports


class ESP32UARTReader:
    def __init__(self, port="/dev/ttyTHS1", baudrate=115200, timeout=2.0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.connected = False
        self.last_reading = None

    def find_port(self) -> str:
        """Mencari port serial yang tersedia jika port default gagal."""
        ports = [p.device for p in serial.tools.list_ports.comports()]
        candidates = [self.port, "/dev/ttyTHS1", "/dev/ttyUSB1", "/dev/ttyACM1", "COM3", "COM4"]
        for c in candidates:
            if c in ports:
                return c
        return self.port

    def connect(self) -> bool:
        """Membuka koneksi Serial UART."""
        if self.ser and self.ser.is_open:
            return True

        target_port = self.find_port()
        try:
            self.ser = serial.Serial(
                port=target_port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            self.port = target_port
            self.connected = True
            print(f"[UART] Terhubung ke ESP32 pada {self.port} @ {self.baudrate} bps")
            return True
        except Exception as e:
            print(f"[UART Error] Gagal membuka port serial {target_port}: {e}")
            self.connected = False
            return False

    def read_telemetry(self) -> dict:
        """
        Membaca 1 baris JSON dari Serial UART ESP32.
        Format JSON dari ESP32:
        {"temp": 28.5, "moisture": 45.2, "ec": 350, "ph": 6.8, "n": 45, "p": 30, "k": 60}
        atau
        {"temperature": 28.5, "moisture": 45.2, "ec": 350, "ph": 6.8, "nitrogen": 45, "phosphor": 30, "kalium": 60}
        """
        if not self.connected or not self.ser or not self.ser.is_open:
            if not self.connect():
                return self.last_reading

        try:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                start_idx = line.find('{')
                end_idx = line.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = line[start_idx:end_idx + 1]
                    raw_data = json.loads(json_str)
                    
                    # Normalisasi key agar kompatibel dengan UI Dashboard & DB
                    normalized = {
                        "nitrogen": raw_data.get("nitrogen", raw_data.get("n", 0)),
                        "phosphor": raw_data.get("phosphor", raw_data.get("p", 0)),
                        "kalium": raw_data.get("kalium", raw_data.get("k", 0)),
                        "ph": raw_data.get("ph", 7.0),
                        "ec": raw_data.get("ec", 0),
                        "moisture": raw_data.get("moisture", 0),
                        "temperature": raw_data.get("temperature", raw_data.get("temp", 0)),
                    }
                    # Simpan data mentah lainnya jika ada (seperti gas MQ/TGS)
                    for k, v in raw_data.items():
                        if k not in normalized:
                            normalized[k] = v

                    self.last_reading = normalized
                    return normalized
        except Exception as e:
            print(f"[UART Parse Error] Gagal membaca data JSON: {e}")
            self.connected = False

        return self.last_reading

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False


if __name__ == "__main__":
    reader = ESP32UARTReader(port="/dev/ttyTHS1", baudrate=115200)
    print("Mulai membaca data serial RX/TX dari ESP32...")
    while True:
        try:
            data = reader.read_telemetry()
            if data:
                print(f"[{time.strftime('%H:%M:%S')}] Data Sensor: {data}")
            time.sleep(1)
        except KeyboardInterrupt:
            break
        except Exception as err:
            print(f"Error: {err}")
            time.sleep(2)
    reader.close()
