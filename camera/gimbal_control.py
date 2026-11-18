#!/usr/bin/env python3
"""
Gimbal Controller - Modul Pengontrol Gimbal 3-Axis via I2C PCA9685
===================================================================
Modul ini digunakan pada Jetson Nano untuk menggerakkan 3 buah servo
(Pan/Yaw, Tilt/Pitch, Roll) menggunakan driver PCA9685 16-channel 12-bit PWM.

Fitur:
- Kontrol halus (smooth movement/interpolation) untuk mencegah lonjakan arus
- Preset arah: Kiri, Kanan, Atas, Bawah, Serong (Diagonal), dan Home (Tengah)
- Kalibrasi sudut minimum/maksimum untuk keamanan mekanis
- CLI interaktif untuk pengujian langsung
"""

import time
import sys
import os
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

## PENGATURAN LOGIKA DEPENDENCY
try:
    import board
    import busio
    from adafruit_pca9685 import PCA9685
    from adafruit_motor import servo
    HAS_LIBS = True
except ImportError:
    HAS_LIBS = False

try:
    import smbus
    HAS_SMBUS = True
except ImportError:
    try:
        import smbus2 as smbus
        HAS_SMBUS = True
    except ImportError:
        HAS_SMBUS = False


class NativeI2CPCA9685:
    """Pure Python Linux /dev/i2c-* PCA9685 Driver using standard fcntl ioctl."""
    I2C_SLAVE = 0x0703
    MODE1 = 0x00
    PRESCALE = 0xFE
    LED0_ON_L = 0x06

    def __init__(self, bus_id=1, address=0x40, freq=50):
        self.bus_path = f"/dev/i2c-{bus_id}"
        self.address = address
        self.freq = freq
        self.fd = None
        self.reconnect()

    def reconnect(self):
        try:
            if self.fd is not None:
                try: os.close(self.fd)
                except Exception: pass
            self.fd = os.open(self.bus_path, os.O_RDWR)
            fcntl.ioctl(self.fd, self.I2C_SLAVE, self.address)
            
            # Reset PCA9685
            self.write_byte(self.MODE1, 0x00)
            time.sleep(0.01)
            
            # Set 50Hz prescale (Servo 20ms period)
            prescale_val = int(25000000.0 / (4096.0 * self.freq) - 1.0 + 0.5)
            old_mode = self.read_byte(self.MODE1)
            new_mode = (old_mode & 0x7F) | 0x10
            self.write_byte(self.MODE1, new_mode)
            self.write_byte(self.PRESCALE, prescale_val)
            self.write_byte(self.MODE1, old_mode)
            time.sleep(0.005)
            self.write_byte(self.MODE1, old_mode | 0xA1)
        except Exception as e:
            print(f"[PCA9685 INIT/RECONNECT ERROR] {e}")

    def write_byte(self, reg, val):
        try:
            if self.fd is not None:
                os.write(self.fd, bytes([reg & 0xFF, val & 0xFF]))
        except Exception as e:
            print(f"[PCA9685 WRITE ERROR] {e}")

    def read_byte(self, reg):
        try:
            if self.fd is not None:
                os.write(self.fd, bytes([reg & 0xFF]))
                return os.read(self.fd, 1)[0]
        except Exception:
            pass
        return 0

    def set_pwm(self, channel, on, off):
        reg = self.LED0_ON_L + 4 * channel
        data = bytes([
            reg & 0xFF,
            on & 0xFF,
            (on >> 8) & 0xFF,
            off & 0xFF,
            (off >> 8) & 0xFF
        ])
        try:
            if self.fd is not None:
                os.write(self.fd, data)
        except Exception as e:
            print(f"[PCA9685 I2C GLITCH] {e}, auto-recovering I2C bus...")
            try:
                self.reconnect()
                if self.fd is not None:
                    os.write(self.fd, data)
            except Exception as e2:
                print(f"[PCA9685 RECONNECT FAIL] {e2}")

    def set_servo_angle(self, channel, angle, min_pulse=500, max_pulse=2500):
        angle = max(0, min(180, angle))
        pulse_us = min_pulse + (angle / 180.0) * (max_pulse - min_pulse)
        off_count = int(pulse_us * 4096.0 / 20000.0)
        self.set_pwm(channel, 0, off_count)

    def close(self):
        try: os.close(self.fd)
        except Exception: pass


class GimbalController:
    """
    Kelas untuk mengontrol gimbal 3-axis menggunakan PCA9685 pada Jetson Nano atau Orange Pi.
    """
    def __init__(self, i2c_bus_id=1, pca_address=0x40, 
                 pan_channel=0, tilt_channel=2, roll_channel=1,
                 min_pulse=500, max_pulse=2500):
        """
        Inisialisasi Controller Gimbal.
        
        Args:
            i2c_bus_id: ID Bus I2C Jetson Nano (default: 1) atau Orange Pi (auto-detects 2)
            pca_address: Alamat I2C driver PCA9685 (default: 0x40)
            pan_channel: Channel servo untuk gerakan horizontal/pan/yaw (default: 0)
            tilt_channel: Channel servo untuk gerakan vertikal/tilt/pitch (default: 2)
            roll_channel: Channel servo untuk gerakan memutar/roll (default: 1)
            min_pulse: Lebar pulsa minimum servo (mikrodetik, default 500)
            max_pulse: Lebar pulsa maksimum servo (mikrodetik, default 2500)
        """
        import os
        # Auto-detect I2C bus containing the PCA9685 address by probing
        detected_bus = None
        if HAS_SMBUS:
            try:
                import smbus
                # Probe buses in prioritized order (bus 2 is typical for Orange Pi, 1 for Jetson, etc.)
                for b_id in [2, 1, 0, 6]:
                    if os.path.exists(f'/dev/i2c-{b_id}'):
                        try:
                            bus_obj = smbus.SMBus(b_id)
                            # Probe the address (read mode register 0x00)
                            bus_obj.read_byte_data(pca_address, 0x00)
                            detected_bus = b_id
                            bus_obj.close()
                            break
                        except Exception:
                            pass
            except Exception:
                pass
        
        if detected_bus is not None:
            i2c_bus_id = detected_bus
        else:
            if i2c_bus_id == 1 and not os.path.exists('/dev/i2c-1') and os.path.exists('/dev/i2c-2'):
                i2c_bus_id = 2

        self.pan_ch = pan_channel
        self.tilt_ch = tilt_channel
        self.roll_ch = roll_channel
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        
        self.use_smbus = not HAS_LIBS and HAS_SMBUS
        self.simulated = not (HAS_LIBS or HAS_SMBUS)

        # Batasan Sudut Aman Servo (Gimbal protection)
        self.pan_limit = (0, 180)     # Sudut Pan (Kiri - Kanan)
        self.tilt_limit = (0, 180)    # Sudut Tilt (Atas - Bawah)
        self.roll_limit = (0, 180)    # Sudut Roll (Kemiringan)

        # Default Homing Setpoints & Pulse Parameters
        self.home_pan = 90
        self.home_tilt = 90
        self.home_roll = 90

        # Load gimbal_calibration.json jika tersedia
        import json
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gimbal_calibration.json")
        if not os.path.exists(cfg_path):
            cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gimbal_calibration.json")
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, 'r') as f:
                    cdata = json.load(f)
                    hdata = cdata.get('home_angles', {})
                    self.home_pan = hdata.get('pan', 90)
                    self.home_tilt = hdata.get('tilt', 90)
                    self.home_roll = hdata.get('roll', 90)
                    self.min_pulse = cdata.get('min_pulse_us', self.min_pulse)
                    self.max_pulse = cdata.get('max_pulse_us', self.max_pulse)
                    self.pan_ch = cdata.get('pan_channel', self.pan_ch)
                    self.tilt_ch = cdata.get('tilt_channel', self.tilt_ch)
                    self.roll_ch = cdata.get('roll_channel', self.roll_ch)
            except Exception as e:
                print(f"Warning loading gimbal_calibration.json: {e}")

        # Sudut Awal (Home Setpoint)
        self.pan_angle = self.home_pan
        self.tilt_angle = self.home_tilt
        self.roll_angle = self.home_roll

        # Kecepatan Perubahan Sudut (Semakin kecil semakin halus)
        self.step_delay = 0.015  # Delay dalam detik setiap pergeseran 1 derajat


        self.use_native = False
        self.native_pca = None

        if HAS_LIBS:
            try:
                # Menggunakan library busio untuk inisialisasi I2C pada Jetson Nano
                self.i2c = busio.I2C(board.SCL, board.SDA)
                self.pca = PCA9685(self.i2c, address=pca_address)
                self.pca.frequency = 50  # Servo standar menggunakan frekuensi 50Hz
                
                # Inisialisasi Servo di masing-masing channel
                self.servo_pan = servo.Servo(self.pca.channels[self.pan_ch], 
                                             min_pulse=self.min_pulse, max_pulse=self.max_pulse)
                self.servo_tilt = servo.Servo(self.pca.channels[self.tilt_ch], 
                                               min_pulse=self.min_pulse, max_pulse=self.max_pulse)
                self.servo_roll = servo.Servo(self.pca.channels[self.roll_ch], 
                                               min_pulse=self.min_pulse, max_pulse=self.max_pulse)
                
                # Gerakkan ke posisi Home saat mulai
                self.go_home()
                print("Hardware Gimbal (Adafruit) berhasil diinisialisasi.")
            except Exception as e:
                print(f"Error saat inisialisasi hardware PCA9685 (Adafruit): {e}")
                if HAS_SMBUS:
                    print("Mencoba fallback ke MODE SMBus...")
                    self.use_smbus = True
                else:
                    self.simulated = True

        if self.use_smbus and not HAS_LIBS:
            try:
                self.smbus_bus = smbus.SMBus(i2c_bus_id)
                self.pca_address = pca_address
                # Reset PCA9685
                self.smbus_bus.write_byte_data(self.pca_address, 0x00, 0x00)
                time.sleep(0.01)
                # Set frequency to 50Hz
                freq_hz = 50
                prescaleval = 25000000.0 / 4096.0 / float(freq_hz) - 1.0
                prescale = int(round(prescaleval))
                oldmode = self.smbus_bus.read_byte_data(self.pca_address, 0x00)
                sleepmode = (oldmode & 0x7F) | 0x10
                self.smbus_bus.write_byte_data(self.pca_address, 0x00, sleepmode)
                self.smbus_bus.write_byte_data(self.pca_address, 0xFE, prescale)
                time.sleep(0.005)
                self.smbus_bus.write_byte_data(self.pca_address, 0x00, oldmode)
                time.sleep(0.005)
                self.smbus_bus.write_byte_data(self.pca_address, 0x00, oldmode | 0xa1)
                
                # Gerakkan ke posisi Home saat mulai
                self.go_home()
                print(f"Hardware Gimbal (SMBus via /dev/i2c-{i2c_bus_id}) berhasil diinisialisasi.")
            except Exception as e:
                print(f"Error saat inisialisasi SMBus PCA9685: {e}")
                self.simulated = True
                self.use_smbus = False

        if not HAS_LIBS and not self.use_smbus and HAS_FCNTL:
            for b_id in [1, 2, 0, 6]:
                if os.path.exists(f'/dev/i2c-{b_id}'):
                    try:
                        self.native_pca = NativeI2CPCA9685(b_id, pca_address)
                        self.use_native = True
                        self.simulated = False
                        print(f"Hardware Gimbal (Native Linux /dev/i2c-{b_id}) berhasil diinisialisasi!")
                        self.go_home()
                        break
                    except Exception as ex:
                        print(f"Native I2C bus {b_id} probe error: {ex}")

        if self.simulated:
            print("Memulai controller dalam MODE SIMULASI (Virtual Gimbal).")

    def get_channel_num(self, servo_type):
        if servo_type == 'pan':
            return self.pan_ch
        elif servo_type == 'tilt':
            return self.tilt_ch
        elif servo_type == 'roll':
            return self.roll_ch
        return 0

    def set_smbus_servo_angle(self, channel, angle):
        if not hasattr(self, 'smbus_bus') or self.smbus_bus is None:
            return
        pulse_us = self.min_pulse + (angle / 180.0) * (self.max_pulse - self.min_pulse)
        pulse_count = int(round(pulse_us * 4096.0 / 20000.0))
        
        on_l = 0x06 + 4 * channel
        on_h = 0x07 + 4 * channel
        off_l = 0x08 + 4 * channel
        off_h = 0x09 + 4 * channel
        
        try:
            self.smbus_bus.write_byte_data(self.pca_address, on_l, 0)
            self.smbus_bus.write_byte_data(self.pca_address, on_h, 0)
            self.smbus_bus.write_byte_data(self.pca_address, off_l, pulse_count & 0xFF)
            self.smbus_bus.write_byte_data(self.pca_address, off_h, pulse_count >> 8)
        except Exception as e:
            print(f"Error writing to SMBus PCA9685: {e}")

    def set_angle(self, servo_type, target_angle, smooth=True):
        if servo_type == 'pan':
            min_a, max_a = self.pan_limit
            target_angle = max(min_a, min(max_a, target_angle))
            current_angle = self.pan_angle
            servo_obj = getattr(self, 'servo_pan', None)
        elif servo_type == 'tilt':
            min_a, max_a = self.tilt_limit
            target_angle = max(min_a, min(max_a, target_angle))
            current_angle = self.tilt_angle
            servo_obj = getattr(self, 'servo_tilt', None)
        elif servo_type == 'roll':
            min_a, max_a = self.roll_limit
            target_angle = max(min_a, min(max_a, target_angle))
            current_angle = self.roll_angle
            servo_obj = getattr(self, 'servo_roll', None)
        else:
            return

        if smooth and current_angle != target_angle:
            step = 1 if target_angle > current_angle else -1
            for angle in range(int(current_angle), int(target_angle) + step, step):
                if not self.simulated:
                    if self.use_native and self.native_pca:
                        self.native_pca.set_servo_angle(self.get_channel_num(servo_type), angle, self.min_pulse, self.max_pulse)
                    elif self.use_smbus:
                        self.set_smbus_servo_angle(self.get_channel_num(servo_type), angle)
                    elif servo_obj:
                        servo_obj.angle = angle
                time.sleep(self.step_delay)
        else:
            if not self.simulated:
                if self.use_native and self.native_pca:
                    self.native_pca.set_servo_angle(self.get_channel_num(servo_type), target_angle, self.min_pulse, self.max_pulse)
                elif self.use_smbus:
                    self.set_smbus_servo_angle(self.get_channel_num(servo_type), target_angle)
                elif servo_obj:
                    servo_obj.angle = target_angle

        if servo_type == 'pan':
            self.pan_angle = target_angle
        elif servo_type == 'tilt':
            self.tilt_angle = target_angle
        elif servo_type == 'roll':
            self.roll_angle = target_angle

    def move_coordinates(self, pan_target, tilt_target, roll_target=90, smooth=False):
        p_start, p_end = self.pan_angle, max(self.pan_limit[0], min(self.pan_limit[1], pan_target))
        t_start, t_end = self.tilt_angle, max(self.tilt_limit[0], min(self.tilt_limit[1], tilt_target))
        r_start, r_end = self.roll_angle, max(self.roll_limit[0], min(self.roll_limit[1], roll_target))

        if not smooth:
            self.set_angle('pan', p_end, smooth=False)
            self.set_angle('tilt', t_end, smooth=False)
            self.set_angle('roll', r_end, smooth=False)
            return

        max_diff = max(abs(p_end - p_start), abs(t_end - t_start), abs(r_end - r_start))
        if max_diff == 0:
            return

        steps = int(max_diff)
        for i in range(1, steps + 1):
            ratio = i / steps
            curr_p = p_start + (p_end - p_start) * ratio
            curr_t = t_start + (t_end - t_start) * ratio
            curr_r = r_start + (r_end - r_start) * ratio

            if not self.simulated:
                if self.use_native and self.native_pca:
                    self.native_pca.set_servo_angle(self.pan_ch, curr_p, self.min_pulse, self.max_pulse)
                    self.native_pca.set_servo_angle(self.tilt_ch, curr_t, self.min_pulse, self.max_pulse)
                    self.native_pca.set_servo_angle(self.roll_ch, curr_r, self.min_pulse, self.max_pulse)
                elif self.use_smbus:
                    self.set_smbus_servo_angle(self.pan_ch, curr_p)
                    self.set_smbus_servo_angle(self.tilt_ch, curr_t)
                    self.set_smbus_servo_angle(self.roll_ch, curr_r)
                elif hasattr(self, 'servo_pan') and self.servo_pan:
                    self.servo_pan.angle = curr_p
                    self.servo_tilt.angle = curr_t
                    self.servo_roll.angle = curr_r
            time.sleep(self.step_delay)

        self.pan_angle = p_end
        self.tilt_angle = t_end
        self.roll_angle = r_end
        
        if self.simulated:
            print(f"[SIMULASI] Gimbal bergerak bersamaan ke -> Pan: {p_end}°, Tilt: {t_end}°, Roll: {r_end}°")

    def go_home(self):
        """Reset semua servo ke posisi Homing Setpoint."""
        self.move_coordinates(self.home_pan, self.home_tilt, self.home_roll, smooth=True)


    def move_direction(self, direction, step=15):
        """
        Menggerakkan gimbal berdasarkan arah mata angin / perintah teks.
        
        Args:
            direction: 
                - 'N'  (North / Atas)
                - 'S'  (South / Bawah)
                - 'E'  (East / Kanan)
                - 'W'  (West / Kiri)
                - 'NW' (North-West / Serong Kiri Atas)
                - 'NE' (North-East / Serong Kanan Atas)
                - 'SW' (South-West / Serong Kiri Bawah)
                - 'SE' (South-East / Serong Kanan Bawah)
                - 'HOME' (Tengah)
            step: Besar perubahan sudut per gerakan (default: 15 derajat)
        """
        target_pan = self.pan_angle
        target_tilt = self.tilt_angle
        target_roll = self.roll_angle

        # Pan: Kiri (W) memperkecil sudut, Kanan (E) memperbesar sudut
        # Tilt: Atas (N) memperkecil sudut (tergantung pemasangan gimbal, biasanya memperkecil sudut agar kamera menghadap ke atas), 
        #       Bawah (S) memperbesar sudut (kamera menghadap ke bawah)
        # Roll: Bisa kita tambahkan penyesuaian kemiringan jika diperlukan saat belok (serong) untuk kestabilan gimbal
        
        direction = direction.upper()

        if direction == 'HOME':
            self.go_home()
            return

        # Tentukan koordinat target berdasarkan arah
        if 'N' in direction:  # Atas
            target_tilt -= step
        if 'S' in direction:  # Bawah
            target_tilt += step
        if 'W' in direction:  # Kiri
            target_pan += step  # Menggeser ke Kiri (Pan bertambah)
        if 'E' in direction:  # Kanan
            target_pan -= step  # Menggeser ke Kanan (Pan berkurang)

        # Roll effect opsional saat bergerak serong (misal sedikit miring agar stabil)
        if direction in ['NW', 'SW']:
            target_roll = 75   # Miring kiri sedikit
        elif direction in ['NE', 'SE']:
            target_roll = 105  # Miring kanan sedikit
        else:
            target_roll = 90   # Stabil tegak

        # Jalankan gerakan koordinat baru secara halus
        self.move_coordinates(target_pan, target_tilt, target_roll, smooth=True)


# CLI MANUAL TESTING
def main():
    print("=" * 60)
    print("     PENGONTROL GIMBAL 3-AXIS JETSON NANO (PCA9685 I2C)     ")
    print("=" * 60)
    
    gimbal = GimbalController()

    print("\nPetunjuk Penggunaan:")
    print("Masukkan perintah di bawah ini untuk menggerakkan gimbal:")
    print("  w   : Atas (Tilt Up)")
    print("  s   : Bawah (Tilt Down)")
    print("  a   : Kiri (Pan Left)")
    print("  d   : Kanan (Pan Right)")
    print("  wa  : Serong Kiri Atas")
    print("  wd  : Serong Kanan Atas")
    print("  sa  : Serong Kiri Bawah")
    print("  sd  : Serong Kanan Bawah")
    print("  h   : Reset ke Tengah (Home)")
    print("  q   : Keluar Program")
    print("=" * 60)

    try:
        while True:
            cmd = input("\nMasukkan perintah -> ").strip().lower()
            if cmd == 'q':
                print("Menutup program gimbal. Sampai jumpa!")
                gimbal.go_home()
                break
            elif cmd == 'w':
                print("Menggerakkan ke: ATAS")
                gimbal.move_direction('N')
            elif cmd == 's':
                print("Menggerakkan ke: BAWAH")
                gimbal.move_direction('S')
            elif cmd == 'a':
                print("Menggerakkan ke: KIRI")
                gimbal.move_direction('W')
            elif cmd == 'd':
                print("Menggerakkan ke: KANAN")
                gimbal.move_direction('E')
            elif cmd in ['wa', 'aw']:
                print("Menggerakkan ke: SERONG KIRI ATAS")
                gimbal.move_direction('NW')
            elif cmd in ['wd', 'dw']:
                print("Menggerakkan ke: SERONG KANAN ATAS")
                gimbal.move_direction('NE')
            elif cmd in ['sa', 'as']:
                print("Menggerakkan ke: SERONG KIRI BAWAH")
                gimbal.move_direction('SW')
            elif cmd in ['sd', 'ds']:
                print("Menggerakkan ke: SERONG KANAN BAWAH")
                gimbal.move_direction('SE')
            elif cmd == 'h':
                print("Mereset ke posisi HOME")
                gimbal.go_home()
            else:
                # Periksa apakah user memasukkan custom koordinat, e.g. "90,60,90"
                try:
                    coords = [float(x) for x in cmd.split(',')]
                    if len(coords) == 3:
                        print(f"Menggerakkan ke Sudut Custom -> Pan: {coords[0]}°, Tilt: {coords[1]}°, Roll: {coords[2]}°")
                        gimbal.move_coordinates(coords[0], coords[1], coords[2])
                    elif len(coords) == 2:
                        print(f"Menggerakkan ke Sudut Custom -> Pan: {coords[0]}°, Tilt: {coords[1]}°")
                        gimbal.move_coordinates(coords[0], coords[1], 90)
                    else:
                        print("Format tidak dikenali. Masukkan w/a/s/d/wa/wd/sa/sd/h/q ATAU sudut custom 'pan,tilt,roll'.")
                except ValueError:
                    print("Format tidak dikenali. Masukkan w/a/s/d/wa/wd/sa/sd/h/q ATAU sudut custom 'pan,tilt,roll'.")

            # Tampilkan info posisi saat ini
            print(f"Posisi Saat Ini -> Pan: {gimbal.pan_angle}°, Tilt: {gimbal.tilt_angle}°, Roll: {gimbal.roll_angle}°")

    except KeyboardInterrupt:
        print("\nProgram dihentikan paksa. Mereset ke posisi Home...")
        gimbal.go_home()


if __name__ == '__main__':
    main()
