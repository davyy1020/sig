import time
import math
import threading

try:
    import Jetson.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO = None
    GPIO_AVAILABLE = False


class AccelStepperJetson:
    """
    Stepper Motor Driver dengan Profil Akselerasi Trapesium (Trapezoidal Velocity Profile).
    Dikembangkan khusus untuk Driver TB6600 & Level Shifter TXS0108E di Jetson Nano.
    """
    def __init__(self, step_pin, dir_pin, ena_pin, name="Stepper"):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.ena_pin = ena_pin
        self.name = name
        self.current_position = 0
        self.lock = threading.Lock()

        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BOARD)
                GPIO.setwarnings(False)
                GPIO.setup(self.step_pin, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.dir_pin, GPIO.OUT, initial=GPIO.LOW)
                GPIO.setup(self.ena_pin, GPIO.OUT, initial=GPIO.HIGH)
            except Exception as e:
                print(f"[{self.name}] GPIO Setup warning: {e}")

    def enable(self, state=True):
        if GPIO_AVAILABLE:
            try:
                GPIO.output(self.ena_pin, GPIO.LOW if state else GPIO.HIGH)
                time.sleep(0.005)
            except Exception:
                pass

    def run_to_position(self, target_steps, max_speed=2000, accel=1500, direction=True):
        """
        Bergerak halus dengan profil akselerasi trapezoidal (Ramp Up & Ramp Down).
        - target_steps : Total langkah (misal: 800 steps)
        - max_speed    : Kecepatan puncak (steps/detik)
        - accel        : Percepatan (steps/detik^2)
        - direction    : True (CW / Atas / Kanan) | False (CCW / Bawah / Kiri)
        """
        if target_steps <= 0:
            return

        with self.lock:
            if GPIO_AVAILABLE:
                self.enable(True)
                GPIO.output(self.dir_pin, GPIO.HIGH if direction else GPIO.LOW)
                time.sleep(0.001)

            min_speed = 50.0  # Kecepatan awal rendah agar tidak hentakan awal
            accel_steps = int((max_speed**2 - min_speed**2) / (2 * accel))

            if target_steps < (2 * accel_steps):
                accel_steps = target_steps // 2
                top_speed = math.sqrt(min_speed**2 + 2 * accel * accel_steps)
            else:
                top_speed = max_speed

            decel_start_step = target_steps - accel_steps

            print(f"[{self.name}] Gerak {target_steps} steps | Top Speed: {top_speed:.0f} stp/s | Dir: {'CW' if direction else 'CCW'}")

            for step in range(target_steps):
                # 1. Ramp Up (Akselerasi)
                if step < accel_steps:
                    current_speed = math.sqrt(min_speed**2 + 2 * accel * step)
                # 2. Ramp Down (Deselerasi)
                elif step >= decel_start_step:
                    steps_remaining = target_steps - step
                    current_speed = math.sqrt(min_speed**2 + 2 * accel * steps_remaining)
                # 3. Constant Speed
                else:
                    current_speed = top_speed

                current_speed = max(current_speed, min_speed)
                step_delay = (1.0 / current_speed) / 2.0

                if GPIO_AVAILABLE:
                    GPIO.output(self.step_pin, GPIO.HIGH)
                    time.sleep(step_delay)
                    GPIO.output(self.step_pin, GPIO.LOW)
                    time.sleep(step_delay)
                else:
                    time.sleep(step_delay * 2)

            if direction:
                self.current_position += target_steps
            else:
                self.current_position -= target_steps


class DualStepperGimbal:
    """
    Controller 2 Motor Stepper NEMA 17 via TB6600 & TXS0108E untuk Kamera 2:
    - Stepper 1 (Tilt Atas/Bawah): Pin 29 (STEP), Pin 31 (DIR), Pin 33 (ENA)
    - Stepper 2 (Pan Kanan/Kiri):   Pin 35 (STEP), Pin 37 (DIR), Pin 36 (ENA)
    """
    def __init__(self, m1_step=29, m1_dir=31, m1_ena=33, m2_step=35, m2_dir=37, m2_ena=36):
        self.stepper_tilt = AccelStepperJetson(m1_step, m1_dir, m1_ena, name="Stepper 1 (Tilt Atas/Bawah)")
        self.stepper_pan  = AccelStepperJetson(m2_step, m2_dir, m2_ena, name="Stepper 2 (Pan Kanan/Kiri)")
        self.is_moving = False
        self.lock = threading.Lock()

    def move_direction(self, direction, steps=800, max_speed=2000, accel=1500):
        """
        Pilihan Arah Pergerakan Joystick:
        - 'UP' / 'N' / 'ATAS'     : Stepper 1 (Tilt Atas)
        - 'DOWN' / 'S' / 'BAWAH'   : Stepper 1 (Tilt Bawah)
        - 'LEFT' / 'W' / 'KIRI'    : Stepper 2 (Pan Kiri)
        - 'RIGHT' / 'E' / 'KANAN'  : Stepper 2 (Pan Kanan)
        - 'HOME'                   : Reset Homing Position
        """
        d = str(direction).upper().strip()
        
        def _worker():
            with self.lock:
                self.is_moving = True
                try:
                    if d in ['UP', 'N', 'ATAS']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                    elif d in ['DOWN', 'S', 'BAWAH']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                    elif d in ['LEFT', 'W', 'KIRI']:
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                    elif d in ['RIGHT', 'E', 'KANAN']:
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                    elif d in ['NW', 'UP_LEFT']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                    elif d in ['NE', 'UP_RIGHT']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                    elif d in ['SW', 'DOWN_LEFT']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=True)
                    elif d in ['SE', 'DOWN_RIGHT']:
                        self.stepper_tilt.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                        self.stepper_pan.run_to_position(steps, max_speed=max_speed, accel=accel, direction=False)
                    elif d == 'HOME':
                        pos_tilt = self.stepper_tilt.current_position
                        pos_pan = self.stepper_pan.current_position
                        if pos_tilt != 0:
                            self.stepper_tilt.run_to_position(abs(pos_tilt), max_speed=max_speed, accel=accel, direction=(pos_tilt < 0))
                        if pos_pan != 0:
                            self.stepper_pan.run_to_position(abs(pos_pan), max_speed=max_speed, accel=accel, direction=(pos_pan < 0))
                finally:
                    self.is_moving = False

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return True

    def get_status(self):
        return {
            "is_moving": self.is_moving,
            "tilt_position": self.stepper_tilt.current_position,
            "pan_position": self.stepper_pan.current_position
        }

    def disable_all(self):
        self.stepper_tilt.enable(False)
        self.stepper_pan.enable(False)
