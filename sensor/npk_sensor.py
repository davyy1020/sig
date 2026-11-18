"""
NPK Sensor Driver - NiuBoL NBL-S-TMC-8 Soil Integrated Sensor
============================================================
Handles dummy simulation mode and physical RS485 Modbus RTU communication.
"""

import random
import time
import serial
import serial.tools.list_ports


class DummyNPKSensor:
    """Simulator sensor NPK 7-in-1 (dummy data)."""
    RANGES = {
        "nitrogen":    {"min": 50,   "max": 350,  "type": "int",   "unit": "mg/kg"},
        "phosphor":    {"min": 20,   "max": 250,  "type": "int",   "unit": "mg/kg"},
        "kalium":      {"min": 50,   "max": 400,  "type": "int",   "unit": "mg/kg"},
        "ph":          {"min": 4.0,  "max": 8.5,  "type": "float", "unit": ""},
        "ec":          {"min": 100,  "max": 1500, "type": "int",   "unit": "µS/cm"},
        "moisture":    {"min": 10.0, "max": 85.0, "type": "float", "unit": "%"},
        "temperature": {"min": 20.0, "max": 38.0, "type": "float", "unit": "°C"},
        "mq3_ppm":     {"min": 0.05, "max": 2.50, "type": "float", "unit": "PPM"},
        "mq3_dig":     {"min": 0,    "max": 0,    "type": "int",   "unit": ""},
        "mq135_ppm":   {"min": 5.0,  "max": 45.0, "type": "float", "unit": "PPM"},
        "mq135_dig":   {"min": 0,    "max": 0,    "type": "int",   "unit": ""},
        "mq138_ppm":   {"min": 0.1,  "max": 3.0,  "type": "float", "unit": "PPM"},
        "mq138_dig":   {"min": 0,    "max": 0,    "type": "int",   "unit": ""},
        "tgs2600_ppm": {"min": 0.2,  "max": 5.0,  "type": "float", "unit": "PPM"},
        "tgs2600_dig": {"min": 0,    "max": 0,    "type": "int",   "unit": ""},
        "tgs2602_ppm": {"min": 0.1,  "max": 2.8,  "type": "float", "unit": "PPM"},
        "tgs2602_dig": {"min": 0,    "max": 0,    "type": "int",   "unit": ""},
    }

    def __init__(self):
        self.connected = True
        self.last_reading = None

    def connect(self) -> bool:
        time.sleep(0.1)
        self.connected = True
        return True

    def get_status(self) -> str:
        return "Connected" if self.connected else "Disconnected"

    def read_sensor(self) -> dict:
        if not self.connected:
            raise ConnectionError("Sensor tidak terkoneksi.")
        time.sleep(0.3)
        reading = {}
        for param, cfg in self.RANGES.items():
            if cfg["type"] == "int":
                reading[param] = random.randint(cfg["min"], cfg["max"])
            else:
                reading[param] = round(random.uniform(cfg["min"], cfg["max"]), 1)
        self.last_reading = reading
        return reading

    def disconnect(self):
        self.connected = False


class RealNPKSensor:
    """Physical NiuBoL 8-in-1 Modbus RTU RS485 Soil Integrated Sensor."""
    
    def __init__(self, port="COM3", baudrate=9600, slave_id=1):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.connected = False
        self.ser = None
        self.last_reading = None


    def calculate_crc(self, data: bytes) -> bytes:
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return crc.to_bytes(2, byteorder='little')

    def connect(self) -> bool:
        """Find and connect to active COM ports."""
        if self.ser and self.ser.is_open:
            return True

        # Search for available COM ports
        ports = [p.device for p in serial.tools.list_ports.comports()]
        
        # Prioritize specified port, but try all others
        target_ports = []
        if self.port:
            target_ports.append(self.port)
        for p in ports:
            if p not in target_ports:
                target_ports.append(p)
                
        if not target_ports:
            # Fallback if list_ports is empty
            target_ports = ["COM1", "COM2", "COM3", "COM4", "/dev/ttyUSB0", "/dev/ttyUSB1"]

        for p in target_ports:
            try:
                self.ser = serial.Serial(
                    port=p,
                    baudrate=self.baudrate,
                    bytesize=8,
                    parity='N',
                    stopbits=1,
                    timeout=1.5
                )
                self.port = p
                self.connected = True
                return True
            except Exception:
                continue
                
        self.connected = False
        return False

    def get_status(self) -> str:
        return "Connected" if self.connected else "Disconnected"

    def read_sensor(self) -> dict:
        """
        Poll data from physical NiuBoL sensor over Modbus.
        Reg 0: Temperature (scaled /10)
        Reg 1: Moisture (scaled /10)
        Reg 2: EC
        Reg 3: pH (scaled /100)
        Reg 4: N
        Reg 5: P
        Reg 6: K
        """
        if not self.connected or self.ser is None or not self.ser.is_open:
            if not self.connect():
                raise ConnectionError("Gagal membuka Port Serial untuk NiuBoL.")

        # Modbus RTU Command: SlaveID, Function 3, Start Address 0x0000, Quantity 8 Registers
        tx_data = bytes([self.slave_id, 3, 0x00, 0x00, 0x00, 0x08])
        tx_frame = tx_data + self.calculate_crc(tx_data)

        self.ser.reset_input_buffer()
        self.ser.write(tx_frame)

        # Expected response size: ID(1) + Func(1) + ByteCount(1) + 8 Regs(16) + CRC(2) = 21 bytes
        expected_len = 21
        rx_frame = self.ser.read(expected_len)

        if not rx_frame:
            raise TimeoutError("Tidak ada respon dari sensor NiuBoL (Timeout).")
            
        if len(rx_frame) < expected_len:
            raise ValueError(f"Respon tidak lengkap. Diterima {len(rx_frame)} dari {expected_len} bytes.")

        if rx_frame[0] != self.slave_id:
            raise ValueError(f"Slave ID tidak cocok. Diterima {rx_frame[0]}, harus {self.slave_id}.")

        if rx_frame[1] == 0x83:
            raise ValueError(f"Modbus Exception: Code 0x{rx_frame[2]:02X}")

        if rx_frame[1] != 3:
            raise ValueError(f"Kode Fungsi tidak cocok. Diterima {rx_frame[1]}, harus 3.")

        # Verify CRC
        calc_crc = self.calculate_crc(rx_frame[:-2])
        recv_crc = rx_frame[-2:]
        if calc_crc != recv_crc:
            raise ValueError("Checksum CRC Modbus gagal.")

        # Parse registers
        t_raw = (rx_frame[3] << 8) | rx_frame[4]
        m_raw = (rx_frame[5] << 8) | rx_frame[6]
        ec = (rx_frame[7] << 8) | rx_frame[8]
        ph_raw = (rx_frame[9] << 8) | rx_frame[10]
        n = (rx_frame[11] << 8) | rx_frame[12]
        p = (rx_frame[13] << 8) | rx_frame[14]
        k = (rx_frame[15] << 8) | rx_frame[16]

        # Scaling
        if t_raw > 32767:
            t_raw -= 65536
        temp = round(t_raw / 10.0, 1)
        moisture = round(m_raw / 10.0, 1)
        ph = round(ph_raw / 100.0, 2)

        self.last_reading = {
            "temperature": temp,
            "moisture": moisture,
            "ec": ec,
            "ph": ph,
            "nitrogen": n,
            "phosphor": p,
            "kalium": k
        }
        return self.last_reading

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False
