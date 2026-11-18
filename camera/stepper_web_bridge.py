import time
import os
import sys
import threading
import serial
import serial.tools.list_ports

class StepperWebBridge:
    """
    Python Serial Bridge antara Flask Web Server (Jetson Nano) & Arduino Nano.
    Mendukung protokol Arduino Stepper:
      - R / KANAN : Motor Kanan
      - L / KIRI  : Motor Kiri
      - U / ATAS  : Motor Atas
      - D / BAWAH : Motor Bawah
      - STOP / S  : Hentikan motor seketika
    Mendukung fitur: Hold to Move (Tekan terus = gerak, lepas = stop)
    serta durasi terkendali (misal: R 1).
    """
    def __init__(self, baudrate=115200):
        self.baudrate = baudrate
        self.serial_conn = None
        self.lock = threading.Lock()
        self.active_dir = None
        self.auto_stop_timer = None
        self.read_thread = None
        self.running = True
        self.last_reconnect_time = 0.0
        
        self.connect_serial()
        # Jalankan background reader agar buffer serial selalu bersih
        self.read_thread = threading.Thread(target=self._read_worker, daemon=True)
        self.read_thread.start()

    def find_arduino_port(self):
        # Prioritas port yang umum dipakai di Jetson Nano & PC
        candidates = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyTHS1', 'COM19', 'COM3', 'COM4']
        try:
            ports = [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            ports = []
        
        for c in candidates:
            if c in ports or (sys.platform.startswith('linux') and os.path.exists(c)):
                return c
        if ports:
            return ports[0]
        return None

    def connect_serial(self):
        with self.lock:
            if self.serial_conn and self.serial_conn.is_open:
                return True
                
            port = self.find_arduino_port()
            if not port:
                return False

            try:
                print(f"[STEPPER BRIDGE] Menghubungkan ke Arduino pada {port} @ {self.baudrate} baud...")
                self.serial_conn = serial.Serial(port, self.baudrate, timeout=0.2)
                time.sleep(1.8) # Jeda waktu DTR reset Arduino
                print(f"[STEPPER BRIDGE SUCCESS] Terhubung ke Arduino pada {port}!")
                return True
            except Exception as e:
                print(f"[STEPPER BRIDGE ERROR] Gagal membuka port {port}: {e}")
                self.serial_conn = None
                return False

    def _read_worker(self):
        """Membaca log/respons dari Arduino agar buffer serial selalu bersih."""
        while self.running:
            try:
                line = None
                with self.lock:
                    if self.serial_conn and self.serial_conn.is_open:
                        if self.serial_conn.in_waiting:
                            line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[ARDUINO RX] {line}")
                time.sleep(0.05)
            except Exception:
                time.sleep(0.5)

    def send_cmd(self, cmd_str):
        with self.lock:
            if not self.serial_conn or not self.serial_conn.is_open:
                now = time.time()
                if now - self.last_reconnect_time < 3.0:
                    return False
                self.last_reconnect_time = now
                port = self.find_arduino_port()
                if port:
                    try:
                        self.serial_conn = serial.Serial(port, self.baudrate, timeout=0.2)
                        time.sleep(1.8)
                    except Exception as e:
                        print(f"[STEPPER RECONNECT FAIL] {e}")
                        return False
                else:
                    return False

            try:
                msg = f"{cmd_str}\n".encode('utf-8')
                self.serial_conn.write(msg)
                self.serial_conn.flush()
                return True
            except Exception as e:
                print(f"[STEPPER BRIDGE TX ERROR] {e}")
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
                self.serial_conn = None
                return False

    def start_move(self, direction, duration=None):
        """
        Direction: 'RIGHT' (R / Kanan), 'LEFT' (L / Kiri),
                   'UP' (U / Atas), 'DOWN' (D / Bawah)
        """
        dir_upper = str(direction).upper().strip()
        # Arah Pan (Kiri/Kanan) dibalik agar pergerakan fisik motor stepper TB6600
        # sesuai dengan tombol Web UI (Tombol Kiri -> Fisik Kiri, Tombol Kanan -> Fisik Kanan)
        cmd_map = {
            'RIGHT': 'L',
            'KANAN': 'L',
            'E': 'L',
            'LEFT': 'R',
            'KIRI': 'R',
            'W': 'R',
            'UP': 'U',
            'ATAS': 'U',
            'N': 'U',
            'DOWN': 'D',
            'BAWAH': 'D',
            'S': 'D',
            'NW': 'U',
            'NE': 'U',
            'SW': 'D',
            'SE': 'D'
        }
        
        # Batalkan timer auto-stop sebelumnya
        if self.auto_stop_timer and self.auto_stop_timer.is_alive():
            self.auto_stop_timer.cancel()

        if dir_upper == 'HOME':
            return self.stop_move()

        cmd = cmd_map.get(dir_upper)
        if not cmd:
            print(f"[STEPPER BRIDGE] Arah tidak dikenal: {direction}")
            return False

        if duration and duration > 0:
            full_cmd = f"{cmd} {duration:.2f}"
        else:
            full_cmd = cmd

        self.active_dir = cmd
        ok = self.send_cmd(full_cmd)
        print(f"[STEPPER BRIDGE] START MOVE -> {direction} ({full_cmd}) : {'OK' if ok else 'FAIL'}")

        # Safety watchdog: jika tombol ditahan lebih dari 8 detik tanpa dilepas, otomatis stop
        if not duration:
            self.auto_stop_timer = threading.Timer(8.0, self.stop_move)
            self.auto_stop_timer.daemon = True
            self.auto_stop_timer.start()

        return ok

    def stop_move(self):
        """Hentikan semua gerakan motor seketika."""
        if self.auto_stop_timer and self.auto_stop_timer.is_alive():
            self.auto_stop_timer.cancel()

        self.active_dir = None
        ok = self.send_cmd("STOP")
        if not ok:
            ok = self.send_cmd("S")
        print(f"[STEPPER BRIDGE] STOP MOVE -> RELEASED : {'OK' if ok else 'FAIL'}")
        return ok

# Singleton instance
stepper_bridge = StepperWebBridge()
