import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;3000000|max_delay;500000"
import sys

# Add Jetson user site-packages and project root to sys.path before any library imports
if os.path.exists('/home/sigma/.local/lib/python3.6/site-packages'):
    sys.path.insert(0, '/home/sigma/.local/lib/python3.6/site-packages')
if os.path.exists('/home/sigma'):
    sys.path.insert(0, '/home/sigma')

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'camera'))

import time
import json
import threading
import requests
import cv2
import glob
import random
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response, send_from_directory

# Import backend classes
from database.db_handler import DatabaseHandler
from api.api_handler import APIHandler

# I2C Servo Gimbal (PCA9685) dinonaktifkan sesuai permintaan pengguna (hanya Arduino Stepper yang aktif)
GimbalController = None

try:
    from camera.stepper_control import DualStepperGimbal
except ImportError:
    try:
        from stepper_control import DualStepperGimbal
    except ImportError:
        DualStepperGimbal = None

try:
    from sensor.npk_sensor import RealNPKSensor, DummyNPKSensor
except ImportError:
    RealNPKSensor = None
    DummyNPKSensor = None

try:
    from sensor.esp32_uart_reader import ESP32UARTReader
except ImportError:
    ESP32UARTReader = None

try:
    from camera.vigi_zoom import VigiOpticalZoomController
except ImportError:
    try:
        from vigi_zoom import VigiOpticalZoomController
    except ImportError:
        VigiOpticalZoomController = None

app = Flask(__name__)

# Create directories
images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
os.makedirs(images_dir, exist_ok=True)

api_url = os.environ.get("SERVER_API_URL", "http://localhost:8000/api/upload.php")
db = DatabaseHandler()
api = APIHandler(base_url=api_url)


# ── ESP32 Sensor Data Buffer ───────────────────────────────────────────────────
# ESP32 pushes sensor readings via HTTP POST to /api/sensor/push or via UART Serial (/dev/ttyTHS1).
# Flask stores the latest reading here, so /api/sensor/read can serve it.
class ESP32SensorBuffer:
    """
    Thread-safe buffer yang menyimpan sensor reading terbaru dari ESP32.
    ESP32 melakukan HTTP POST atau UART Serial RX/TX → disimpan di sini.
    /api/sensor/read membaca dari buffer ini.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._data = None
        self._timestamp = None

    def update(self, data: dict):
        """Simpan data sensor terbaru dari ESP32."""
        with self._lock:
            self._data = data.copy()
            self._timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get(self):
        """Ambil data sensor terbaru beserta timestamp terima."""
        with self._lock:
            if self._data is None:
                return None, None
            return self._data.copy(), self._timestamp

    def is_available(self) -> bool:
        """Cek apakah ada data yang sudah diterima dari ESP32."""
        with self._lock:
            return self._data is not None

esp32_uart_buffer = ESP32SensorBuffer()
esp32_wifi_buffer = ESP32SensorBuffer()
real_npk_sensor = RealNPKSensor() if RealNPKSensor is not None else None
dummy_npk_sensor = DummyNPKSensor() if DummyNPKSensor is not None else None

# Background UART Listener Thread untuk membaca ESP32 dari RX/TX (/dev/ttyTHS1)
def _start_uart_listener():
    if ESP32UARTReader is None:
        return
    reader = ESP32UARTReader(port="/dev/ttyTHS1", baudrate=115200)
    print("[UART Listener] Background thread started for Jetson Nano /dev/ttyTHS1...")
    while True:
        try:
            data = reader.read_telemetry()
            if data:
                esp32_uart_buffer.update(data)
        except Exception as err:
            pass
        time.sleep(1.0)

uart_listener_thread = threading.Thread(target=_start_uart_listener, daemon=True)
uart_listener_thread.start()

# ── Camera Configuration ───────────────────────────────────────────────────────
# Kamera TP-Link VIGI RTSP Camera (192.168.136.108) sebagai kamera utama aktif
_env_cam2 = os.environ.get("CAMERA2_SOURCE", "rtsp://admin:sigma123@192.168.136.108:554/stream2")
try:
    DEFAULT_CAMERA2_SOURCE = int(_env_cam2)
except ValueError:
    DEFAULT_CAMERA2_SOURCE = _env_cam2

DEFAULT_CAMERA_SOURCE = DEFAULT_CAMERA2_SOURCE

class WebCameraHandler:
    def __init__(self):
        self.camera_index = DEFAULT_CAMERA_SOURCE
        self.running = False
        self.paused = False
        self.capture = None
        self.lock = threading.RLock()
        self.current_frame = None
        self.current_jpeg = None
        self.frame_seq = 0
        self.thread = None
        
        # States untuk recording & virtual PTZ
        self.recording = False
        self.video_writer = None
        self.pan_offset = 0
        self.tilt_offset = 0

        # Physical Gimbal Controller (I2C Servo dinonaktifkan)
        self.gimbal = None

    def start(self, source=None):
        if source is None or str(source).strip() in ["", "/api/camera/stream", "default"]:
            source = DEFAULT_CAMERA_SOURCE

        try:
            target_source = int(source)
        except (ValueError, TypeError):
            target_source = str(source).strip()

        with self.lock:
            # If already running with the exact same source, do not kill the thread!
            if self.running and str(self.camera_index) == str(target_source) and self.capture and self.capture.isOpened():
                print(f"[CAM] Camera already streaming on {target_source}, keeping alive.")
                return

            if self.running:
                self._stop_thread()

            self.camera_index = target_source
            self.running = True
            self.paused = False
            self.current_frame = None
            self.current_jpeg = None
            self.pan_offset = 0
            self.tilt_offset = 0
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()

    def _open_capture(self):
        """Open or reconnect VideoCapture with low buffer and proper backends."""
        try:
            if self.capture:
                try:
                    self.capture.release()
                except Exception:
                    pass
                self.capture = None

            is_rtsp = isinstance(self.camera_index, str) and self.camera_index.startswith('rtsp')

            # 1. On Jetson Linux, use hardware-accelerated zero-latency GStreamer for RTSP
            if is_rtsp and sys.platform.startswith("linux"):
                try:
                    from urllib.parse import urlsplit, unquote
                    parsed = urlsplit(self.camera_index)
                    endpoint = f"rtsp://{parsed.hostname}:{parsed.port or 554}{parsed.path}"
                    user = unquote(parsed.username or "")
                    password = unquote(parsed.password or "")
                    gst_pipeline = (
                        f'rtspsrc location="{endpoint}" user-id="{user}" user-pw="{password}" protocols=tcp latency=50 '
                        f'drop-on-latency=true tcp-timeout=5000000 ! rtph264depay ! h264parse ! nvv4l2decoder ! '
                        f'nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! '
                        f'appsink max-buffers=1 drop=true sync=false'
                    )
                    print(f"[CAM GST] Opening low-latency hardware GStreamer for {endpoint}...")
                    cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
                    if cap.isOpened():
                        print(f"[CAM GST SUCCESS] Hardware accelerated zero-latency RTSP connected!")
                        self.capture = cap
                        return
                    else:
                        print(f"[CAM GST WARN] GStreamer failed, falling back to standard backend.")
                except Exception as gst_err:
                    print(f"[CAM GST ERROR] {gst_err}, falling back...")

            # 2. Standard backend fallback
            if sys.platform.startswith("linux") and isinstance(self.camera_index, int):
                self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
            else:
                self.capture = cv2.VideoCapture(self.camera_index)

            if is_rtsp and self.capture:
                self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            print(f"[CAM OPEN ERROR] {self.camera_index}: {e}")
            self.capture = None

    def _run(self):
        import numpy as np

        try:
            is_http = isinstance(self.camera_index, str) and self.camera_index.startswith('http')
            is_rtsp = isinstance(self.camera_index, str) and self.camera_index.startswith('rtsp')

            if is_http:
                import requests
                target_urls = [self.camera_index]
                if "192.168.136.100" in str(self.camera_index):
                    target_urls.append("http://192.168.136.1:5000/api/camera/stream")
                
                url_idx = 0
                retry_count = 0
                while self.running:
                    curr_url = target_urls[url_idx % len(target_urls)]
                    print(f"[CAM HTTP] Connecting to HTTP MJPEG stream {curr_url}...")
                    try:
                        req_stream = requests.get(curr_url, stream=True, timeout=3)
                        if req_stream.status_code == 200:
                            print(f"[CAM HTTP SUCCESS] Connected to {curr_url}!")
                            retry_count = 0
                            bytes_data = b''
                            for chunk in req_stream.iter_content(chunk_size=8192):
                                if not self.running:
                                    break
                                if self.paused:
                                    time.sleep(0.05)
                                    continue

                                bytes_data += chunk
                                a = bytes_data.find(b'\xff\xd8')
                                if a != -1:
                                    if a > 0:
                                        bytes_data = bytes_data[a:]
                                    b = bytes_data.find(b'\xff\xd9', 2)
                                    if b != -1:
                                        jpg = bytes_data[:b+2]
                                        bytes_data = bytes_data[b+2:]
                                        with self.lock:
                                            self.current_jpeg = jpg
                                        frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                                        if frame is not None:
                                            with self.lock:
                                                self.current_frame = frame.copy()
                                                if self.recording and self.video_writer is not None:
                                                    self.video_writer.write(frame)
                        else:
                            print(f"[CAM HTTP WARN] HTTP status {req_stream.status_code}, retrying...")
                            retry_count += 1
                            if retry_count >= 2:
                                url_idx += 1
                                retry_count = 0
                            time.sleep(1)
                    except Exception as e:
                        print(f"[CAM HTTP RECONNECTING] {e}, trying next URL...")
                        retry_count += 1
                        if retry_count >= 2:
                            url_idx += 1
                            retry_count = 0
                        time.sleep(1)
                return

            # ── RTSP / OpenCV Hardware Camera ─────────────────────────────
            print(f"[CAM] Opening camera source: {self.camera_index}...")
            self._open_capture()

            retry_count = 0
            while self.running:
                if self.paused:
                    time.sleep(0.05)
                    continue

                if self.capture is None or not self.capture.isOpened():
                    time.sleep(0.5)
                    self._open_capture()
                    continue

                ret, frame = self.capture.read()
                if not ret or frame is None:
                    retry_count += 1
                    if retry_count % 20 == 0:
                        print(f"[CAM WARN] Failed to read frame from {self.camera_index} ({retry_count}/30)...")
                    if retry_count >= 30:
                        print(f"[CAM WATCHDOG] Stream stalled on {self.camera_index}, force reconnecting...")
                        if self.capture:
                            try:
                                self.capture.release()
                            except Exception:
                                pass
                            self.capture = None
                        retry_count = 0
                        time.sleep(0.5)
                        continue
                    time.sleep(0.05)
                    continue
                else:
                    retry_count = 0

                # Virtual PTZ (only when digital pan/tilt offset is active)
                if self.pan_offset != 0 or self.tilt_offset != 0:
                    h, w, _ = frame.shape
                    crop_w = w - 120
                    crop_h = h - 90
                    if crop_w > 0 and crop_h > 0:
                        x_start = (w - crop_w) // 2
                        y_start = (h - crop_h) // 2
                        with self.lock:
                            po = self.pan_offset
                            to = self.tilt_offset
                        x_start = max(0, min(w - crop_w, x_start + po))
                        y_start = max(0, min(h - crop_h, y_start + to))
                        cropped = frame[y_start:y_start+crop_h, x_start:x_start+crop_w]
                        frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

                # Pre-encode JPEG once for high performance zero-lag streaming
                ret_enc, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                with self.lock:
                    self.current_frame = frame.copy()
                    if ret_enc:
                        self.current_jpeg = buf.tobytes()
                    self.frame_seq += 1
                    if self.recording and self.video_writer is not None:
                        self.video_writer.write(frame)

                if not is_rtsp:
                    time.sleep(0.03)

        except Exception as e:
            print("Camera error in thread:", e)
        finally:
            self.stop_recording()
            if self.capture:
                self.capture.release()
                self.capture = None

    def pause(self):
        with self.lock:
            self.paused = not self.paused
        return self.paused

    def stop(self):
        self._stop_thread()

    def _stop_thread(self):
        self.stop_recording()
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
            self.thread = None
        if self.capture:
            try:
                self.capture.release()
            except Exception:
                pass
            self.capture = None
        with self.lock:
            self.current_frame = None

    def capture_frame(self, save_dir, blok="default", scale=1.0):
        with self.lock:
            if self.current_frame is None:
                return ""
            frame = self.current_frame.copy()

        # Crop & zoom frame if scale > 1.0 to match screen zoom/scale
        try:
            scale_val = float(scale)
            if scale_val > 1.0 and frame is not None:
                h, w, _ = frame.shape
                crop_w = int(w / scale_val)
                crop_h = int(h / scale_val)
                if crop_w > 0 and crop_h > 0:
                    x_start = max(0, (w - crop_w) // 2)
                    y_start = max(0, (h - crop_h) // 2)
                    cropped = frame[y_start:y_start+crop_h, x_start:x_start+crop_w]
                    frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)
        except Exception as e:
            print("Error applying capture scale:", e)

        os.makedirs(save_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        pattern = os.path.join(save_dir, f"{date_str}_{blok}_*.jpg")
        existing_files = glob.glob(pattern)
        
        next_number = 1
        if existing_files:
            numbers = []
            for f in existing_files:
                basename = os.path.basename(f)
                try:
                    name_part = os.path.splitext(basename)[0]
                    num_str = name_part.rsplit("_", 1)[-1]
                    numbers.append(int(num_str))
                except (ValueError, IndexError):
                    continue
            if numbers:
                next_number = max(numbers) + 1

        filename = f"{date_str}_{blok}_{next_number:03d}.jpg"
        filepath = os.path.join(save_dir, filename)
        
        # Save frame with 100% Maximum Uncompressed JPEG Quality
        success = cv2.imwrite(filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
        if success:
            return os.path.abspath(filepath)
        return ""

    def start_recording(self, save_dir, blok="default"):
        with self.lock:
            if not self.running:
                self.running = True
            
            if getattr(self, 'recording', False):
                return getattr(self, 'current_video_path', "")
            
            os.makedirs(save_dir, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Clean blok name for file system safety
            blok_clean = "".join(c for c in blok if c.isalnum() or c in ('-', '_')).strip()
            if not blok_clean:
                blok_clean = "default"
                
            raw_filename = f"raw_REC_{date_str}_{blok_clean}_{int(time.time())}.avi"
            filepath = os.path.join(save_dir, raw_filename)
            
            # Setup VideoWriter matching capture dimensions dynamically
            w, h = 1280, 720
            if self.current_frame is not None:
                h, w, _ = self.current_frame.shape
            elif self.capture and self.capture.isOpened():
                w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
                h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
                
            # MJPG FourCC in AVI container is 100% stable and produces zero FFmpeg PTS/DTS errors
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (w, h))
            self.recording = True
            self.current_video_path = os.path.abspath(filepath)

            # Launch background recording loop thread
            self._rec_thread = threading.Thread(target=self._record_worker, args=(w, h), daemon=True)
            self._rec_thread.start()
            print(f"[RECORDING STARTED] Saving raw frames to {self.current_video_path}")
            return self.current_video_path

    def _record_worker(self, w, h):
        """Worker thread to record frames continuously at 20 FPS."""
        while getattr(self, 'recording', False) and getattr(self, 'video_writer', None) is not None:
            frame_to_write = None
            with self.lock:
                if self.current_frame is not None:
                    frame_to_write = self.current_frame.copy()

            if frame_to_write is None:
                # Generate synthetic recording frame if camera frame is unavailable
                frame_to_write = np.zeros((h, w, 3), dtype=np.uint8)
                frame_to_write[:] = (35, 20, 15)
                cv2.putText(frame_to_write, "REC ● LIVE STREAM", (40, 60),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                t_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                cv2.putText(frame_to_write, t_str, (40, h - 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

            try:
                writer = getattr(self, 'video_writer', None)
                if writer is not None and writer.isOpened():
                    writer.write(frame_to_write)
            except Exception as e:
                print("[RECORDING ERR]", e)
            time.sleep(0.04)  # ~25 FPS

    def stop_recording(self):
        saved_path = ""
        with self.lock:
            saved_path = getattr(self, 'current_video_path', "")
            self.recording = False

        # Gracefully wait for recording worker thread to completely exit first
        if hasattr(self, '_rec_thread') and self._rec_thread and self._rec_thread.is_alive():
            try:
                self._rec_thread.join(timeout=2.0)
            except Exception:
                pass

        with self.lock:
            if getattr(self, 'video_writer', None) is not None:
                try:
                    self.video_writer.release()
                except Exception as ex:
                    print("[RELEASE ERR]", ex)
                finally:
                    self.video_writer = None
            print(f"[RECORDING STOPPED] Saved to {saved_path}")
            return saved_path

    def move_camera(self, direction):
        # 1. Physical Gimbal movement
        if hasattr(self, 'gimbal') and self.gimbal is not None:
            try:
                threading.Thread(target=self.gimbal.move_direction, args=(direction, 15), daemon=True).start()
            except Exception as e:
                print(f"Failed to move physical gimbal: {e}")

        # 2. Virtual Crop Fallback
        with self.lock:
            step = 15
            if direction == "N":
                self.tilt_offset -= step
            elif direction == "S":
                self.tilt_offset += step
            elif direction == "W":
                self.pan_offset -= step
            elif direction == "E":
                self.pan_offset += step
            elif direction == "NW":
                self.tilt_offset -= step
                self.pan_offset -= step
            elif direction == "NE":
                self.tilt_offset -= step
                self.pan_offset += step
            elif direction == "SW":
                self.tilt_offset += step
                self.pan_offset -= step
            elif direction == "SE":
                self.tilt_offset += step
                self.pan_offset += step
            elif direction == "HOME":
                self.pan_offset = 0
                self.tilt_offset = 0

camera_handler = WebCameraHandler()
camera_handler2 = WebCameraHandler()
stepper_gimbal = DualStepperGimbal() if DualStepperGimbal is not None else None
vigi_zoom_controller = VigiOpticalZoomController() if VigiOpticalZoomController is not None else None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

videos_dir = os.path.join(project_root, "videos")
os.makedirs(videos_dir, exist_ok=True)

# Endpoint to serve saved camera photos
@app.route('/images/<path:filename>')
@app.route('/ui/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(images_dir, filename)

# Endpoint to serve saved camera videos with proper streaming headers
@app.route('/videos/<path:filename>')
def serve_video(filename):
    mimetype = "video/mp4"
    if filename.endswith(".webm"):
        mimetype = "video/webm"
    elif filename.endswith(".avi"):
        mimetype = "video/x-msvideo"
    elif filename.endswith(".mkv"):
        mimetype = "video/x-matroska"
    resp = send_from_directory(videos_dir, filename, mimetype=mimetype)
    resp.headers['Accept-Ranges'] = 'bytes'
    return resp

# Step 1 Location API Helper & Endpoint
def fetch_location_with_fallback():
    # Primary default target: Dafam Express Jaksa, Menteng, Jakarta Pusat
    default_lat = -6.185300
    default_lon = 106.829300
    default_address = "Dafam Express Jaksa, Jalan Jaksa No. 27–29, Menteng, Jakarta Pusat, DKI Jakarta"

    lat_val = 0.0
    lon_val = 0.0
    detailed_address = ""

    # Provider 1: ipinfo.io
    try:
        r = requests.get('https://ipinfo.io/json', timeout=3)
        if r.status_code == 200:
            d = r.json()
            loc = d.get('loc', '')
            if ',' in loc:
                lat, lon = loc.split(',')
                lat_val = float(lat)
                lon_val = float(lon)
                city = d.get('city', '')
                region = d.get('region', '')
                country = d.get('country', '')
                detailed_address = ", ".join(filter(None, [city, region, country]))
    except Exception:
        pass

    # Provider 2: ip-api.com (if Provider 1 failed)
    if lat_val == 0.0 and lon_val == 0.0:
        try:
            r = requests.get('http://ip-api.com/json/', timeout=3)
            if r.status_code == 200:
                d = r.json()
                if d.get('status') == 'success':
                    lat_val = float(d.get('lat', 0.0))
                    lon_val = float(d.get('lon', 0.0))
                    city = d.get('city', '')
                    region = d.get('regionName', '')
                    country = d.get('country', '')
                    detailed_address = ", ".join(filter(None, [city, region, country]))
        except Exception:
            pass

    # Provider 3: ipapi.co (if Providers 1 & 2 failed)
    if lat_val == 0.0 and lon_val == 0.0:
        try:
            r = requests.get('https://ipapi.co/json/', timeout=3)
            if r.status_code == 200:
                d = r.json()
                lat_val = float(d.get('latitude', 0.0))
                lon_val = float(d.get('longitude', 0.0))
                city = d.get('city', '')
                region = d.get('region', '')
                country = d.get('country_name', '')
                detailed_address = ", ".join(filter(None, [city, region, country]))
        except Exception:
            pass

    # If IP resolution returned ISP gateway (Bekasi or zero), fallback to exact Jaksa Menteng location
    if lat_val == 0.0 or (abs(lat_val - (-6.23)) < 0.08 and abs(lon_val - 106.98) < 0.08):
        lat_val = default_lat
        lon_val = default_lon
        detailed_address = default_address
    else:
        # Reverse geocoding via Nominatim if valid lat/lon retrieved
        try:
            geo_url = f"https://nominatim.openstreetmap.org/reverse?lat={lat_val}&lon={lon_val}&format=json&accept-language=id"
            geo_headers = {'User-Agent': 'SistemMonitoringKebun/1.0'}
            geo_r = requests.get(geo_url, headers=geo_headers, timeout=3)
            if geo_r.status_code == 200:
                geo_data = geo_r.json()
                display_name = geo_data.get('display_name', '')
                if display_name:
                    detailed_address = display_name
        except Exception:
            pass

    if not detailed_address:
        detailed_address = default_address

    return lat_val, lon_val, detailed_address


@app.route('/api/location', methods=['POST'])
def get_location():
    try:
        lat_val, lon_val, detailed_address = fetch_location_with_fallback()
        return jsonify({
            "success": True,
            "latitude": lat_val,
            "longitude": lon_val,
            "nama_lokasi": detailed_address
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "latitude": -6.185300,
            "longitude": 106.829300,
            "nama_lokasi": "Dafam Express Jaksa, Jalan Jaksa No. 27–29, Menteng, Jakarta Pusat, DKI Jakarta"
        })

# Step 2 Camera APIs
@app.route('/api/camera/start', methods=['POST'])
def start_camera():
    data = request.json or {}
    source = data.get("source", None)
    if source is None or str(source).strip() in ["", "/api/camera/stream", "default"]:
        source = DEFAULT_CAMERA_SOURCE
    camera_handler.start(source)
    return jsonify({"success": True, "message": "Camera started", "source": str(camera_handler.camera_index)})

@app.route('/api/camera/pause', methods=['POST'])
def pause_camera():
    paused = camera_handler.pause()
    return jsonify({"success": True, "paused": paused})

@app.route('/api/camera/stop', methods=['POST'])
def stop_camera():
    camera_handler.stop()
    return jsonify({"success": True, "message": "Camera stopped"})

@app.route('/api/camera/capture', methods=['GET', 'POST'])
def capture_camera():
    data = request.get_json(silent=True) or {}
    blok = data.get("blok", "default")
    scale = float(data.get("scale", 1.0))
    if not blok:
        blok = "default"
    blok = "".join(c for c in str(blok) if c.isalnum() or c in ('-', '_')).strip() or "default"
    
    filepath = camera_handler2.capture_frame(images_dir, blok, scale=scale)
    if not filepath and camera_handler:
        filepath = camera_handler.capture_frame(images_dir, blok, scale=scale)
    if filepath and os.path.exists(filepath):
        filename = os.path.basename(filepath)
        url = f"/images/{filename}"
        return jsonify({"success": True, "filepath": filepath, "url": url, "filename": filename})

    # Direct Camera Snapshot Fallback (HTTP MJPEG only)
    import requests
    try:
        if str(DEFAULT_CAMERA_SOURCE).startswith("http"):
            print(f"[CAPTURE] Attempting direct snapshot from {DEFAULT_CAMERA_SOURCE}...")
            r = requests.get(DEFAULT_CAMERA_SOURCE, stream=True, timeout=4)
            if r.status_code == 200:
                bytes_data = b''
                for chunk in r.iter_content(8192):
                    bytes_data += chunk
                    a = bytes_data.find(b'\xff\xd8')
                    if a != -1:
                        if a > 0: bytes_data = bytes_data[a:]
                        b = bytes_data.find(b'\xff\xd9', 2)
                        if b != -1:
                            jpg = bytes_data[:b+2]
                            os.makedirs(images_dir, exist_ok=True)
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            import glob as _glob
                            pattern = os.path.join(images_dir, f"{date_str}_{blok}_*.jpg")
                            existing = _glob.glob(pattern)
                            next_num = 1
                            if existing:
                                nums = []
                                for f in existing:
                                    try: nums.append(int(os.path.splitext(os.path.basename(f))[0].rsplit("_", 1)[-1]))
                                    except: pass
                            if nums: next_num = max(nums) + 1
                        filename = f"{date_str}_{blok}_{next_num:03d}.jpg"
                        filepath = os.path.join(images_dir, filename)

                        # Apply crop/scale to direct snapshot if scale > 1.0
                        if scale > 1.0:
                            import cv2
                            import numpy as np
                            frame_decoded = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                            if frame_decoded is not None:
                                h, w, _ = frame_decoded.shape
                                crop_w = int(w / scale)
                                crop_h = int(h / scale)
                                if crop_w > 0 and crop_h > 0:
                                    x_start = max(0, (w - crop_w) // 2)
                                    y_start = max(0, (h - crop_h) // 2)
                                    cropped = frame_decoded[y_start:y_start+crop_h, x_start:x_start+crop_w]
                                    frame_scaled = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)
                                    cv2.imwrite(filepath, frame_scaled, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                                else:
                                    with open(filepath, "wb") as f: f.write(jpg)
                            else:
                                with open(filepath, "wb") as f: f.write(jpg)
                        else:
                            with open(filepath, "wb") as f:
                                f.write(jpg)

                        print(f"[CAPTURE OK] Saved direct snapshot (scale={scale}) to {filepath}")
                        return jsonify({"success": True, "filepath": os.path.abspath(filepath), "url": f"/images/{filename}", "filename": filename})
    except Exception as ex:
        print(f"[CAPTURE FALLBACK ERR] {ex}")

    return jsonify({"success": False, "message": "Gagal mengambil foto. Pastikan kamera terhubung."})

@app.route('/api/camera/capture_canvas', methods=['POST'])
def capture_canvas():
    """Terima JPEG blob dari canvas browser, simpan ke disk."""
    blok = request.form.get("blok", "default").strip()
    blok = "".join(c for c in blok if c.isalnum() or c in ('-', '_')).strip() or "default"
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "message": "No file uploaded."})
    try:
        os.makedirs(images_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        import glob as _glob
        pattern = os.path.join(images_dir, f"{date_str}_{blok}_*.jpg")
        existing = _glob.glob(pattern)
        next_num = 1
        if existing:
            nums = []
            for f in existing:
                try: nums.append(int(os.path.splitext(os.path.basename(f))[0].rsplit("_", 1)[-1]))
                except: pass
            if nums: next_num = max(nums) + 1
        filename = f"{date_str}_{blok}_{next_num:03d}.jpg"
        filepath = os.path.join(images_dir, filename)
        file.save(filepath)
        return jsonify({"success": True, "filepath": os.path.abspath(filepath), "url": f"/images/{filename}", "filename": filename})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

def _post_process_video(filepath):
    """Auto-transcode raw OpenCV video to web-compatible H.264 MP4 format."""
    if not filepath or not os.path.exists(filepath):
        return filepath
    
    if filepath.endswith(".webm"):
        return filepath

    # Allow OS to flush raw file handles safely
    time.sleep(0.25)

    dir_name = os.path.dirname(filepath)
    base_name = os.path.basename(filepath)
    
    if base_name.startswith("raw_"):
        final_name = os.path.splitext(base_name[4:])[0] + ".mp4"
    else:
        name_no_ext = os.path.splitext(base_name)[0]
        final_name = f"{name_no_ext}.mp4"

    final_filepath = os.path.join(dir_name, final_name)
    tmp_path = os.path.join(dir_name, f"tmp_{final_name}")

    try:
        cmd = [
            "ffmpeg", "-y", "-i", filepath,
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            "-preset", "ultrafast", "-crf", "23",
            tmp_path
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        if res.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            import shutil
            if os.path.exists(final_filepath) and final_filepath != tmp_path:
                try: os.remove(final_filepath)
                except Exception: pass
            shutil.move(tmp_path, final_filepath)
            if os.path.exists(filepath) and filepath != final_filepath:
                try: os.remove(filepath)
                except Exception: pass
            print(f"[FFMPEG OK] Transcoded web H.264 video: {final_filepath}")
            return final_filepath
        else:
            print(f"[FFMPEG FAIL] returncode={res.returncode}, stderr={res.stderr.decode('utf-8', 'ignore')}")
            if os.path.exists(tmp_path): os.remove(tmp_path)
    except Exception as e:
        print(f"[FFMPEG CONVERT ERR] {e}")
        if os.path.exists(tmp_path): os.remove(tmp_path)
    return filepath

@app.route('/api/camera/upload_video', methods=['POST'])
def upload_video():
    """Endpoint untuk menerima rekaman video WebM/MP4 dari browser client."""
    blok = request.form.get("blok", "default").strip()
    blok = "".join(c for c in blok if c.isalnum() or c in ('-', '_')).strip() or "default"
    file = request.files.get("file")
    if not file:
        return jsonify({"success": False, "message": "No video file uploaded."})
    try:
        os.makedirs(videos_dir, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = ".webm"
        if file.filename and "." in file.filename:
            ext = "." + file.filename.rsplit(".", 1)[-1]
        filename = f"REC_{date_str}_{blok}_{int(time.time())}{ext}"
        filepath = os.path.join(videos_dir, filename)
        file.save(filepath)
        
        # Post-process if needed for web compatibility
        filepath = _post_process_video(filepath)
        filename = os.path.basename(filepath)

        print(f"[VIDEO UPLOAD OK] Saved browser recording to {filepath}")
        return jsonify({
            "success": True,
            "filepath": os.path.abspath(filepath),
            "url": f"/videos/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/camera/start_recording', methods=['POST'])
def start_recording():
    data = request.get_json(silent=True) or {}
    blok = data.get("blok", "default").strip()
    filepath = camera_handler2.start_recording(videos_dir, blok)
    if not filepath and camera_handler:
        filepath = camera_handler.start_recording(videos_dir, blok)
    if filepath:
        return jsonify({"success": True, "filepath": filepath, "filename": os.path.basename(filepath)})
    return jsonify({"success": False, "message": "Failed to start recording."})

@app.route('/api/camera/stop_recording', methods=['POST'])
def stop_recording():
    saved_path = camera_handler2.stop_recording()
    if not saved_path and camera_handler:
        saved_path = camera_handler.stop_recording()
    if saved_path:
        saved_path = _post_process_video(saved_path)
    filename = os.path.basename(saved_path) if saved_path else ""
    return jsonify({
        "success": True,
        "message": "Recording stopped and video saved",
        "filepath": saved_path,
        "filename": filename,
        "url": f"/videos/{filename}" if filename else ""
    })

@app.route('/api/gimbal/direction', methods=['POST'])
def gimbal_move_direction():
    """Endpoint untuk eksekusi perintah D-Pad arah & Roll dari Web Interface."""
    try:
        data = request.json or {}
        direction = str(data.get("direction", "HOME")).upper()
        step = float(data.get("step", 15.0))

        if hasattr(camera_handler, 'gimbal') and camera_handler.gimbal is not None:
            g = camera_handler.gimbal
            p, t, r = g.pan_angle, g.tilt_angle, g.roll_angle

            if direction == "ROLL_LEFT" or direction == "ROLL_CCW":
                r = max(0.0, min(180.0, r - step))
            elif direction == "ROLL_RIGHT" or direction == "ROLL_CW":
                r = max(0.0, min(180.0, r + step))
            elif direction == "ROLL_FLAT":
                r = 90.0
            elif direction == "HOME":
                g.go_home()
                return jsonify({"success": True, "message": "Gimbal reset to Home Setpoint", "pan": g.pan_angle, "tilt": g.tilt_angle, "roll": g.roll_angle})
            else:
                if 'N' in direction: t = max(0.0, min(180.0, t - step))
                if 'S' in direction: t = max(0.0, min(180.0, t + step))
                if 'W' in direction: p = max(0.0, min(180.0, p + step))
                if 'E' in direction: p = max(0.0, min(180.0, p - step))

            g.move_coordinates(p, t, r, smooth=False)
            return jsonify({"success": True, "message": f"Moved {direction}", "pan": p, "tilt": t, "roll": r})
        else:
            return jsonify({"success": False, "message": "Servo Gimbal PCA9685 hardware controller tidak aktif."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/gimbal/get_calibration', methods=['GET'])
def get_gimbal_calibration():
    """Mengembalikan konfigurasi kalibrasi & setpoint Homing dari JSON."""
    cfg_path = os.path.join(project_root, "gimbal_calibration.json")
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, 'r') as f:
                return jsonify({"success": True, "calibration": json.load(f)})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
    return jsonify({
        "success": True,
        "calibration": {
            "home_angles": {"pan": 90, "tilt": 90, "roll": 90},
            "min_pulse_us": 500,
            "max_pulse_us": 2500
        }
    })


@app.route('/api/gimbal/set_home', methods=['POST'])
def set_gimbal_home():
    """Menyimpan setpoint Homing baru ke file JSON."""
    try:
        data = request.json or {}
        pan = float(data.get("pan", 90))
        tilt = float(data.get("tilt", 90))
        roll = float(data.get("roll", 90))
        min_p = int(data.get("min_pulse", 500))
        max_p = int(data.get("max_pulse", 2500))

        cfg = {
            "pan_channel": 0,
            "tilt_channel": 2,
            "roll_channel": 1,
            "home_angles": {"pan": pan, "tilt": tilt, "roll": roll},
            "min_pulse_us": min_p,
            "max_pulse_us": max_p,
            "i2c_bus": 2,
            "pca_address": "0x40"
        }
        cfg_path = os.path.join(project_root, "gimbal_calibration.json")
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f, indent=4)

        if hasattr(camera_handler, 'gimbal') and camera_handler.gimbal is not None:
            camera_handler.gimbal.home_pan = pan
            camera_handler.gimbal.home_tilt = tilt
            camera_handler.gimbal.home_roll = roll
            camera_handler.gimbal.min_pulse = min_p
            camera_handler.gimbal.max_pulse = max_p

        return jsonify({"success": True, "message": "Homing calibration setpoints saved."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



@app.route('/api/camera/status', methods=['GET'])
def get_camera_status():
    return jsonify({
        "success": True,
        "running": camera_handler.running,
        "paused": camera_handler.paused,
        "recording": camera_handler.recording
    })

@app.route('/api/camera2/status', methods=['GET'])
def get_camera2_status():
    return jsonify({
        "success": True,
        "running": camera_handler2.running,
        "paused": camera_handler2.paused,
        "recording": camera_handler2.recording
    })

def generate_mjpeg_stream():
    """MJPEG generator — Kamera 1 (SICK RTSP Camera)."""
    FRAME_INTERVAL = 1.0 / 25.0  # target 25 FPS
    last_sent = 0.0
    import numpy as np
    blank_frame = np.zeros((480, 640, 3), np.uint8)
    blank_frame[:] = (30, 20, 15)
    cv2.putText(blank_frame, "[!] KAMERA 1 (SICK) OFFLINE", (40, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
    cv2.putText(blank_frame, "Hubungkan Kamera SICK (192.168.136.191)", (40, 260),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    _, blank_buf = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    blank_bytes = blank_buf.tobytes()

    while True:
        now = time.monotonic()
        wait = FRAME_INTERVAL - (now - last_sent)
        if wait > 0:
            time.sleep(wait)
        last_sent = time.monotonic()

        payload = None
        if camera_handler.running and not camera_handler.paused:
            with camera_handler.lock:
                payload = camera_handler.current_jpeg
                if payload is None and camera_handler.current_frame is not None:
                    ret, buffer = cv2.imencode('.jpg', camera_handler.current_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    if ret:
                        payload = buffer.tobytes()

        if payload is None:
            payload = blank_bytes

        try:
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n"
                   b"Content-Length: " + str(len(payload)).encode('ascii') + b"\r\n\r\n" +
                   payload + b"\r\n")
        except (GeneratorExit, BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            break

@app.route('/api/camera/stream')
def camera_stream():
    return Response(generate_mjpeg_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def generate_mjpeg_stream_cam2():
    """MJPEG generator — Kamera 2 (TP-Link VIGI RTSP Stream) Zero-Latency."""
    last_seq = -1
    import numpy as np
    blank_frame = np.zeros((480, 640, 3), np.uint8)
    blank_frame[:] = (30, 20, 15)
    cv2.putText(blank_frame, "[!] KAMERA 2 (TP-LINK) OFFLINE", (40, 220),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
    cv2.putText(blank_frame, "Hubungkan Kamera TP-Link (192.168.136.108)", (40, 260),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    _, blank_buf = cv2.imencode('.jpg', blank_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    blank_bytes = blank_buf.tobytes()

    while True:
        payload = None
        if camera_handler2.running and not camera_handler2.paused:
            with camera_handler2.lock:
                curr_seq = getattr(camera_handler2, 'frame_seq', 0)
                raw_jpg = camera_handler2.current_jpeg
            
            # Jika belum ada frame baru, tunggu sebentar (10ms)
            if curr_seq == last_seq and raw_jpg is not None:
                time.sleep(0.01)
                continue
            
            last_seq = curr_seq
            payload = raw_jpg

        if payload is None:
            payload = blank_bytes
            time.sleep(0.3)

        header = f"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: {len(payload)}\r\n\r\n".encode('ascii')
        try:
            yield header + payload + b'\r\n'
        except (GeneratorExit, BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            break

@app.route('/api/camera2/stream')
def camera2_stream():
    return Response(generate_mjpeg_stream_cam2(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/camera2/capture', methods=['GET', 'POST'])
def capture_photo_camera2():
    try:
        data = request.get_json(silent=True) or {}
        blok = data.get("blok", "TPLINK")
        if not blok:
            blok = "TPLINK"
        blok = "".join(c for c in str(blok) if c.isalnum() or c in ('-', '_')).strip() or "TPLINK"
        saved_path = camera_handler2.capture_frame(images_dir, blok=blok, scale=1.0)
        if not saved_path and camera_handler:
            saved_path = camera_handler.capture_frame(images_dir, blok=blok, scale=1.0)
        if saved_path and os.path.exists(saved_path):
            filename = os.path.basename(saved_path)
            return jsonify({
                "success": True,
                "message": "Snapshot Kamera TP-Link berhasil diambil",
                "filename": filename,
                "url": f"/images/{filename}",
                "filepath": saved_path
            })
        return jsonify({"success": False, "message": "Gagal mengambil frame dari Kamera TP-Link"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# =============================================================================
# OPTICAL ZOOM CONTROLLER (TP-LINK VIGI S345ZI MOTORIZED VARIFOCAL LENS ONVIF)
# =============================================================================
@app.route('/api/camera/optical_zoom', methods=['GET', 'POST'])
def camera_optical_zoom():
    """Endpoint untuk kontrol Optical Zoom fisik TP-Link VIGI S345ZI via ONVIF."""
    if not vigi_zoom_controller:
        return jsonify({"success": False, "message": "VigiOpticalZoomController tidak tersedia"}), 500
    try:
        data = request.get_json(silent=True) or request.args or {}
        action = str(data.get("action", "")).lower().strip()
        step = float(data.get("step", 0.15))
        position = data.get("position")

        if position is not None:
            pos_val = float(position)
            ok, msg = vigi_zoom_controller.zoom_absolute(pos_val)
            return jsonify({"success": ok, "mode": "absolute", "position": pos_val, "message": "Set Optical Zoom Position" if ok else str(msg)})
        elif action in ("in", "tele", "+", "zoomin"):
            ok, msg = vigi_zoom_controller.zoom_step("in", step)
            return jsonify({"success": ok, "mode": "step", "direction": "in", "step": step, "message": "Optical Zoom In (Tele)" if ok else str(msg)})
        elif action in ("out", "wide", "-", "zoomout"):
            ok, msg = vigi_zoom_controller.zoom_step("out", step)
            return jsonify({"success": ok, "mode": "step", "direction": "out", "step": step, "message": "Optical Zoom Out (Wide)" if ok else str(msg)})
        elif action in ("reset", "home", "1x"):
            ok, msg = vigi_zoom_controller.zoom_absolute(0.0)
            return jsonify({"success": ok, "mode": "reset", "position": 0.0, "message": "Optical Zoom Reset to 1.0x (Wide)" if ok else str(msg)})
        elif action in ("stop",):
            ok, msg = vigi_zoom_controller.zoom_stop()
            return jsonify({"success": ok, "mode": "stop", "message": "Optical Zoom Stopped" if ok else str(msg)})
        else:
            return jsonify({"success": False, "message": f"Action '{action}' tidak dikenal. Gunakan 'in', 'out', 'reset', atau berikan 'position' (0.0 - 1.0)"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# =============================================================================
# PAK AHMAD I-GANOSENSE AI INTEGRATION ROUTES (PORT 8080)
# =============================================================================
AI_SERVICE_HOST = os.environ.get("AI_SERVICE_HOST", "127.0.0.1" if sys.platform.startswith("linux") else "192.168.136.138")
AI_SERVICE_PORT = int(os.environ.get("AI_SERVICE_PORT", "8080"))
AI_BASE_URL = f"http://{AI_SERVICE_HOST}:{AI_SERVICE_PORT}"

@app.route('/api/ai/status', methods=['GET'])
def get_ai_status():
    """Proxy status deteksi real-time dari model Pak Ahmad."""
    try:
        r = requests.get(f"{AI_BASE_URL}/status.json", timeout=2.0)
        if r.status_code == 200:
            return jsonify({"success": True, "ai": r.json()})
        return jsonify({"success": False, "message": f"AI service HTTP {r.status_code}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"AI service offline: {e}"}), 503

@app.route('/api/ai/stream')
def get_ai_stream():
    """Proxy live annotated MJPEG stream dari model AI YOLO26n-seg Pak Ahmad."""
    def forward_stream():
        try:
            r = requests.get(f"{AI_BASE_URL}/stream.mjpg", stream=True, timeout=5)
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        except Exception:
            pass
    return Response(forward_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/ai/capture', methods=['GET', 'POST'])
def capture_ai_photo():
    """Ambil snapshot foto beranotasi AI Ganoderma dan simpan ke galeri Kiosk."""
    try:
        data = request.get_json(silent=True) or {}
        blok = data.get("blok", "AI_GANO")
        blok = "".join(c for c in str(blok) if c.isalnum() or c in ('-', '_')).strip() or "AI_GANO"
        
        # Download snapshot from AI service port 8080
        r = requests.get(f"{AI_BASE_URL}/latest.jpg", timeout=3.0)
        if r.status_code == 200 and len(r.content) > 1000:
            os.makedirs(images_dir, exist_ok=True)
            date_str = datetime.now().strftime("%Y-%m-%d")
            import glob as _glob
            pattern = os.path.join(images_dir, f"{date_str}_{blok}_*.jpg")
            existing = _glob.glob(pattern)
            next_num = 1
            if existing:
                nums = []
                for f in existing:
                    try: nums.append(int(os.path.splitext(os.path.basename(f))[0].rsplit("_", 1)[-1]))
                    except: pass
                if nums: next_num = max(nums) + 1
            filename = f"{date_str}_{blok}_{next_num:03d}.jpg"
            filepath = os.path.join(images_dir, filename)
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"[AI CAPTURE OK] Saved AI snapshot to {filepath}")
            return jsonify({
                "success": True,
                "message": "Snapshot AI Ganoderma berhasil diambil",
                "filename": filename,
                "url": f"/images/{filename}",
                "filepath": filepath
            })
        else:
            # Fallback to standard camera2 capture if AI snapshot not ready
            return capture_photo_camera2()
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Stepper Motor Pan/Tilt Control APIs (Arduino Serial Bridge)
@app.route('/api/stepper/status', methods=['GET'])
def get_stepper_status():
    bridge = get_stepper_bridge()
    connected = bool(bridge and bridge.serial_conn and bridge.serial_conn.is_open)
    return jsonify({
        "success": True,
        "status": {
            "is_moving": bool(bridge and bridge.active_dir),
            "connected": connected,
            "port": bridge.serial_conn.port if (bridge and bridge.serial_conn) else None,
            "direction": bridge.active_dir if bridge else None
        }
    })

# Step 3 Sensor APIs
@app.route('/api/sensor/push', methods=['POST'])
def push_sensor_data():
    """
    Endpoint yang menerima data sensor dari ESP32 via HTTP POST.
    ESP32 mengirim JSON payload secara periodik dari IP static-nya.
    
    Expected JSON from ESP32:
    {
        "nitrogen": 48, "phosphor": 55, "kalium": 72,
        "ph": 6.20, "ec": 185, "moisture": 42.50, "temperature": 28.70
    }
    """
    try:
        data = request.json or {}
        if not data:
            return jsonify({"success": False, "message": "Empty payload"}), 400

        # Validasi field yang wajib ada
        required_fields = ["nitrogen", "phosphor", "kalium", "ph", "ec", "moisture", "temperature"]
        missing = [f for f in required_fields if f not in data]
        if missing:
            return jsonify({
                "success": False,
                "message": f"Field tidak lengkap: {', '.join(missing)}"
            }), 400

        # Simpan ke WiFi buffer
        esp32_wifi_buffer.update(data)

        print(f"[ESP32 WiFi] Data sensor diterima: N={data.get('nitrogen')} P={data.get('phosphor')} "
              f"K={data.get('kalium')} pH={data.get('ph')} EC={data.get('ec')} "
              f"Moist={data.get('moisture')}% Temp={data.get('temperature')}°C")

        return jsonify({"success": True, "message": "Data sensor WiFi berhasil diterima"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/sensor/read', methods=['POST'])
def read_sensor_data():
    """
    Endpoint yang dibaca oleh dashboard browser untuk menampilkan data sensor.
    Prioritas Pembacaan:
    1. Data dari ESP32 Hardware Serial UART (/dev/ttyTHS1 - Pin 2 & 4) -> mode "ESP32 SERIAL RX/TX REAL"
    2. Data Push dari ESP32 via WiFi HTTP POST (/api/sensor/push) -> mode "ESP32 WIFI HTTP REAL"
    3. Modbus RS485 Langsung di Device (RealNPKSensor) -> mode "RS485 HARDWARE MODBUS"
    4. Simulator Dummy (DummyNPKSensor) -> Fallback "MOCK SIMULATED"
    """
    try:
        # 1. Cek Data Serial UART (Pin 2 & 4 /dev/ttyTHS1)
        data_uart, timestamp_uart = esp32_uart_buffer.get()
        if data_uart is not None:
            return jsonify({
                "success": True,
                "reading": data_uart,
                "mode": "ESP32 SERIAL RX/TX REAL",
                "received_at": timestamp_uart
            })

        # 2. Cek Data Push WiFi HTTP (POST /api/sensor/push)
        data_wifi, timestamp_wifi = esp32_wifi_buffer.get()
        if data_wifi is not None:
            return jsonify({
                "success": True,
                "reading": data_wifi,
                "mode": "ESP32 WIFI HTTP REAL",
                "received_at": timestamp_wifi
            })

        # 2. Cek Modbus RS485 Fisik Langsung
        if real_npk_sensor is not None:
            try:
                reading = real_npk_sensor.read_sensor()
                if reading:
                    return jsonify({
                        "success": True,
                        "reading": reading,
                        "mode": "RS485 HARDWARE MODBUS",
                        "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            except Exception as rs485_err:
                print(f"[Sensor] Direct RS485 read failed: {rs485_err}")

        # 3. Fallback ke Simulator Dummy
        if dummy_npk_sensor is not None:
            dummy_reading = dummy_npk_sensor.read_sensor()
            # Pastikan field RAW ADC gas terisi untuk testing/simulasi jika ESP32 belum online
            dummy_reading.setdefault("mq3_raw", int(dummy_reading.get("mq3_ppm", 1.2) * 350))
            dummy_reading.setdefault("mq135_raw", int(dummy_reading.get("mq135_ppm", 15.0) * 45))
            dummy_reading.setdefault("mq138_raw", int(dummy_reading.get("mq138_ppm", 1.5) * 400))
            dummy_reading.setdefault("tgs2600_raw", int(dummy_reading.get("tgs2600_ppm", 2.0) * 300))
            dummy_reading.setdefault("tgs2602_raw", int(dummy_reading.get("tgs2602_ppm", 1.1) * 350))
            return jsonify({
                "success": True,
                "reading": dummy_reading,
                "mode": "MOCK SIMULATED",
                "received_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        return jsonify({
            "success": False,
            "message": "Tidak ada sensor fisik atau ESP32 yang terhubung."
        }), 503

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/sensor/status', methods=['GET'])
def get_sensor_status():
    """Cek status koneksi sensor (ESP32, RS485, atau Mock)."""
    try:
        data_uart, ts_uart = esp32_uart_buffer.get()
        data_wifi, ts_wifi = esp32_wifi_buffer.get()
        data = data_uart or data_wifi
        timestamp = ts_uart if data_uart else ts_wifi
        mode = "ESP32 SERIAL RX/TX REAL" if data_uart else ("ESP32 WIFI HTTP REAL" if data_wifi else "READY")
        return jsonify({
            "success": True,
            "esp32_connected": data is not None,
            "mode": mode,
            "last_received": timestamp
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "esp32_connected": False,
            "mode": "READY",
            "last_received": None
        })

# Save data
@app.route('/api/inspection/save', methods=['POST'])
def save_inspection():
    try:
        data = request.json or {}
        
        # Validate required fields
        nama_perusahaan = data.get('nama_perusahaan', '').strip()
        nama_kebun = data.get('nama_kebun', '').strip()
        
        if not nama_perusahaan or not nama_kebun:
            return jsonify({
                "success": False, 
                "message": "Form Belum Lengkap! Nama Perusahaan dan Nama Kebun wajib diisi."
            }), 400
            
        # Ensure timestamp is set
        data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        inserted_id = db.insert_inspection(data)
        return jsonify({"success": True, "id": inserted_id, "message": "Data berhasil disimpan!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Step 4 History/List APIs
@app.route('/api/inspection/list', methods=['GET'])
def get_inspections():
    try:
        records = db.get_all_inspections()
        return jsonify({"success": True, "records": records})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/inspection/delete', methods=['POST'])
def delete_inspections():
    try:
        data = request.json or {}
        ids = data.get("ids", [])
        if ids:
            db.delete_multiple(ids)
        return jsonify({"success": True, "message": f"{len(ids)} data berhasil dihapus!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/inspection/upload', methods=['POST'])
def upload_inspections():
    try:
        data = request.json or {}
        ids = data.get("ids", [])
        all_pending = data.get("all_pending", False)
        
        records = db.get_all_inspections()
        if all_pending:
            targets = [row for row in records if not row.get('uploaded', 0)]
        else:
            targets = [row for row in records if row.get('id') in ids]
            
        if not targets:
            return jsonify({"success": True, "uploaded_count": 0, "message": "Tidak ada data pending untuk diunggah."})
            
        success_count = 0
        for row in targets:
            record_id = row.get('id')
            photo_path = row.get('foto_path', None)
            
            upload_data = row.copy()
            if 'foto_path' in upload_data: del upload_data['foto_path']
            if 'uploaded' in upload_data: del upload_data['uploaded']
            
            res = api.upload_inspection(upload_data, photo_path)
            if res.get('success', False):
                db.mark_uploaded(record_id)
                success_count += 1
                
        return jsonify({
            "success": True,
            "uploaded_count": success_count,
            "total_requested": len(targets),
            "message": f"Berhasil mengunggah {success_count} dari {len(targets)} data."
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ── Stepper Web Control API (Hold to move, release to stop) ─────────────────────
def get_stepper_bridge():
    try:
        from camera.stepper_web_bridge import stepper_bridge
        return stepper_bridge
    except Exception:
        try:
            from stepper_web_bridge import stepper_bridge
            return stepper_bridge
        except Exception as e:
            print(f"[STEPPER IMPORT ERROR] {e}")
            return None

@app.route('/api/stepper/move', methods=['POST'])
def api_stepper_move():
    try:
        data = request.json or {}
        direction = data.get("direction", "").upper() # 'RIGHT', 'LEFT', 'UP', 'DOWN'
        action = data.get("action", "start")
        duration = data.get("duration", None)
        if duration is not None:
            try: duration = float(duration)
            except Exception: duration = None
        
        bridge = get_stepper_bridge()
        if not bridge:
            return jsonify({"success": False, "message": "Stepper bridge module not loaded"}), 500
            
        if action == "stop" or direction == "HOME":
            bridge.stop_move()
            return jsonify({"success": True, "status": "stopped"})
        else:
            ok = bridge.start_move(direction, duration=duration)
            return jsonify({"success": ok, "status": "moving", "direction": direction})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/stepper/stop', methods=['POST'])
def api_stepper_stop():
    try:
        bridge = get_stepper_bridge()
        if bridge:
            bridge.stop_move()
        return jsonify({"success": True, "status": "stopped"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    # Auto-start Kamera TP-Link VIGI RTSP Camera
    camera_handler2.start(DEFAULT_CAMERA2_SOURCE)
    app_port = int(os.environ.get("KIOSK_PORT", 5000))
    print(f"[SERVER] Kiosk Web Server berjalan di http://0.0.0.0:{app_port}")
    print(f"[SERVER] Kamera Aktif (TP-Link): {DEFAULT_CAMERA2_SOURCE}")
    print(f"[SERVER] Endpoint ESP32 push data: POST /api/sensor/push")
    app.run(host='0.0.0.0', port=app_port, debug=False, threaded=True)

