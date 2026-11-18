"""
Camera Handler - Modul pengelolaan kamera dengan OpenCV + PyQt5 QThread
=======================================================================
Menyediakan streaming kamera secara real-time dalam thread terpisah,
serta fitur capture frame dan penyimpanan gambar.

Fitur:
- Streaming kamera via QThread dengan target 30 FPS
- Pause/Resume streaming
- Capture dan simpan frame sebagai JPG
- Thread-safe akses frame menggunakan QMutex
- Penanganan error saat kamera tidak tersedia
"""

import cv2
import numpy as np
import os
import glob
from datetime import datetime

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

# Import GimbalController secara dinamis agar aman dijalankan di Windows maupun Jetson Nano
try:
    from camera.gimbal_control import GimbalController
except ImportError:
    try:
        from gimbal_control import GimbalController
    except ImportError:
        GimbalController = None


class CameraThread(QThread):
    """
    Thread kamera yang berjalan di background untuk streaming frame.
    
    Signals:
        frame_signal(np.ndarray): Dipancarkan setiap frame baru dibaca.
        error_signal(str): Dipancarkan saat terjadi error.
        status_signal(str): Dipancarkan saat status kamera berubah.
    
    Penggunaan:
        camera = CameraThread(camera_index=0)
        camera.frame_signal.connect(update_display)
        camera.error_signal.connect(show_error)
        camera.start()
        # ...
        camera.stop()
        camera.wait()
    """

    # Sinyal untuk komunikasi antar-thread
    frame_signal = pyqtSignal(np.ndarray)   # Emit setiap frame baru
    error_signal = pyqtSignal(str)          # Emit pesan error
    status_signal = pyqtSignal(str)         # Emit perubahan status

    # Target FPS untuk streaming
    TARGET_FPS = 30

    def __init__(self, camera_index=0, parent=None):
        """
        Inisialisasi CameraThread.

        Args:
            camera_index: Index kamera (int) atau link RTSP (str).
            parent: Parent QObject (opsional).
        """
        super().__init__(parent)
        self.camera_index = camera_index
        self.running = False
        self.paused = False
        self.capture = None
        self.mutex = QMutex()
        self.current_frame = None
        
        # States untuk recording & virtual PTZ
        self.recording = False
        self.video_writer = None
        self.pan_offset = 0
        self.tilt_offset = 0

        # Inisialisasi Kontrol Gimbal PCA9685
        if GimbalController is not None:
            try:
                self.gimbal = GimbalController()
            except Exception as e:
                print(f"Gagal memproses inisialisasi GimbalController: {e}")
                self.gimbal = None
        else:
            self.gimbal = None

    def run(self):
        """
        Main loop thread kamera.
        Membuka kamera, membaca frame secara kontinu, dan memancarkan sinyal.
        Loop berjalan pada target 30 FPS.
        """
        self.running = True
        self.paused = False

        # Buka kamera
        if sys.platform.startswith("linux") and isinstance(self.camera_index, int):
            self.capture = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
        else:
            self.capture = cv2.VideoCapture(self.camera_index)

        if not self.capture.isOpened():
            error_msg = (
                f"Gagal membuka kamera (index {self.camera_index}). "
                "Pastikan kamera terhubung dan tidak digunakan aplikasi lain."
            )
            self.error_signal.emit(error_msg)
            self.status_signal.emit("Camera Error")
            self.running = False
            return

        # Atur resolusi kamera ke 16:9 (1280x720) untuk tampilan modern dan tajam
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.status_signal.emit("Camera Streaming")

        # Hitung interval antar-frame berdasarkan target FPS
        frame_interval_ms = int(1000 / self.TARGET_FPS)

        while self.running:
            # Jika di-pause, tunggu tanpa membaca frame
            if self.paused:
                self.msleep(100)
                continue

            ret, frame = self.capture.read()

            if not ret:
                # Frame gagal dibaca — bisa jadi kamera dicabut
                self.error_signal.emit("Gagal membaca frame dari kamera.")
                self.status_signal.emit("Camera Error")
                break

            # Rotate camera video feed 180 degrees (kamera dipasang terbalik 180 derajat)
            if frame is not None:
                frame = cv2.rotate(frame, cv2.ROTATE_180)

            # --- Virtual PTZ Crop / Pan & Tilt simulation ---
            h, w, _ = frame.shape
            # Crop slightly zoomed-in frame to allow panning/tilting (e.g. crop 120px off width, 90px off height)
            crop_w = w - 120
            crop_h = h - 90
            if crop_w > 0 and crop_h > 0:
                # Center coords of cropped box
                x_start = (w - crop_w) // 2
                y_start = (h - crop_h) // 2
                
                # Apply pan & tilt offsets
                x_start += self.pan_offset
                y_start += self.tilt_offset
                
                # Clamp within boundaries
                x_start = max(0, min(w - crop_w, x_start))
                y_start = max(0, min(h - crop_h, y_start))
                
                cropped = frame[y_start:y_start+crop_h, x_start:x_start+crop_w]
                frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_LINEAR)

            # Simpan frame saat ini dengan thread-safe mutex
            locker = QMutexLocker(self.mutex)
            self.current_frame = frame.copy()
            del locker  # Lepas mutex segera setelah copy

            # Tulis ke video writer jika sedang merekam
            if self.recording and self.video_writer is not None:
                self.video_writer.write(frame)

            # Pancarkan frame ke slot yang terhubung (misal: UI display)
            self.frame_signal.emit(frame)

            # Delay sesuai target FPS
            self.msleep(frame_interval_ms)

        # Bersihkan recording jika masih aktif saat di-stop
        if self.recording:
            self.stop_recording()

        # Bersihkan resource kamera
        self._release_camera()

    def start_recording(self, save_dir: str = "videos", blok: str = "default") -> str:
        """
        Mulai merekam video feed ke file MP4.
        
        Args:
            save_dir: Direktori penyimpanan video.
            blok: Nama blok untuk nama file.
            
        Returns:
            Path video yang direkam, atau string kosong jika gagal.
        """
        if self.recording:
            return ""

        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            self.error_signal.emit(f"Gagal membuat direktori video '{save_dir}': {e}")
            return ""

        date_str = datetime.now().strftime("%Y-%m-%d")
        pattern = os.path.join(save_dir, f"{date_str}_{blok}_video_*.mp4")
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

        filename = f"{date_str}_{blok}_video_{next_number:03d}.mp4"
        filepath = os.path.abspath(os.path.join(save_dir, filename))

        # Setup VideoWriter matching capture dimensions dynamically
        w, h = 640, 480
        if self.current_frame is not None:
            h, w, _ = self.current_frame.shape
        elif self.capture and self.capture.isOpened():
            w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(filepath, fourcc, 20.0, (w, h))

        if not self.video_writer.isOpened():
            self.error_signal.emit("Gagal membuat file output video.")
            self.video_writer = None
            return ""

        self.recording = True
        self.current_video_path = filepath
        self.status_signal.emit(f"Perekaman dimulai: {filename}")
        return filepath

    def stop_recording(self) -> str:
        """Hentikan perekaman video feed dan kembalikan file path video."""
        if not self.recording:
            return ""
            
        saved_path = getattr(self, 'current_video_path', "")
        self.recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        self.status_signal.emit("Perekaman selesai")
        return saved_path

    def move_camera(self, direction: str):
        """
        Gerakkan kamera secara fisik menggunakan gimbal 3-axis (PCA9685)
        serta jalankan simulasi PTZ crop fallback.
        
        Args:
            direction: Arah gerakan ('NW', 'N', 'NE', 'W', 'HOME', 'E', 'SW', 'S', 'SE')
        """
        # 1. Gerakkan fisik gimbal menggunakan PCA9685 jika terhubung
        if hasattr(self, 'gimbal') and self.gimbal is not None:
            try:
                self.gimbal.move_direction(direction, step=15)
            except Exception as e:
                print(f"Gagal menggerakkan gimbal fisik: {e}")

        # 2. Jalankan simulasi PTZ crop fallback
        step = 10
        if direction == "NW":
            self.pan_offset -= step
            self.tilt_offset -= step
        elif direction == "N":
            self.tilt_offset -= step
        elif direction == "NE":
            self.pan_offset += step
            self.tilt_offset -= step
        elif direction == "W":
            self.pan_offset -= step
        elif direction == "E":
            self.pan_offset += step
        elif direction == "SW":
            self.pan_offset -= step
            self.tilt_offset += step
        elif direction == "S":
            self.tilt_offset += step
        elif direction == "SE":
            self.pan_offset += step
            self.tilt_offset += step
        elif direction == "HOME":
            self.pan_offset = 0
            self.tilt_offset = 0

        # Batasan offset (agar tidak keluar dari batas resolusi original 640x480)
        # Dengan crop_w=520 dan crop_h=390, max pan offset = 60, max tilt offset = 45
        self.pan_offset = max(-60, min(60, self.pan_offset))
        self.tilt_offset = max(-45, min(45, self.tilt_offset))

    def _release_camera(self):
        """Lepaskan resource kamera dengan aman."""
        if self.capture is not None and self.capture.isOpened():
            self.capture.release()
            self.capture = None

    def pause(self):
        """Pause streaming kamera (kamera tetap terbuka)."""
        self.paused = True
        self.status_signal.emit("Camera Paused")

    def resume(self):
        """Lanjutkan streaming setelah di-pause."""
        self.paused = False
        self.status_signal.emit("Camera Streaming")

    def stop(self):
        """
        Hentikan thread kamera.
        Panggil wait() setelah stop() untuk memastikan thread selesai.
        """
        self.running = False
        self.status_signal.emit("Camera Stopped")

    def capture_frame(self, save_dir: str = "images", blok: str = "default", scale: float = 1.0) -> str:
        """
        Ambil dan simpan frame saat ini sebagai file JPG dengan dukungan zoom/scale.
        """
        # Ambil frame saat ini secara thread-safe
        locker = QMutexLocker(self.mutex)
        frame = self.current_frame.copy() if self.current_frame is not None else None
        del locker

        if frame is None:
            self.error_signal.emit("Tidak ada frame untuk disimpan.")
            return ""

        # Crop & zoom frame jika scale > 1.0 agar foto mengikuti zoom/scale tampilan
        if scale > 1.0:
            h, w, _ = frame.shape
            crop_w = int(w / scale)
            crop_h = int(h / scale)
            if crop_w > 0 and crop_h > 0:
                x_start = max(0, (w - crop_w) // 2)
                y_start = max(0, (h - crop_h) // 2)
                cropped = frame[y_start:y_start+crop_h, x_start:x_start+crop_w]
                frame = cv2.resize(cropped, (w, h), interpolation=cv2.INTER_CUBIC)

        # Pastikan direktori penyimpanan ada
        try:
            os.makedirs(save_dir, exist_ok=True)
        except OSError as e:
            self.error_signal.emit(f"Gagal membuat direktori '{save_dir}': {e}")
            return ""

        # Tentukan tanggal untuk penamaan file
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Cari nomor urut berikutnya berdasarkan file yang sudah ada
        # Pattern: YYYY-MM-DD_blok_NNN.jpg
        pattern = os.path.join(save_dir, f"{date_str}_{blok}_*.jpg")
        existing_files = glob.glob(pattern)

        next_number = 1
        if existing_files:
            # Ekstrak nomor terbesar dari file yang ada
            numbers = []
            for f in existing_files:
                basename = os.path.basename(f)
                # Ambil bagian NNN dari nama file
                try:
                    name_part = os.path.splitext(basename)[0]  # Hilangkan .jpg
                    num_str = name_part.rsplit("_", 1)[-1]     # Ambil bagian terakhir
                    numbers.append(int(num_str))
                except (ValueError, IndexError):
                    continue
            if numbers:
                next_number = max(numbers) + 1

        # Buat nama file dengan format NNN (3 digit, zero-padded)
        filename = f"{date_str}_{blok}_{next_number:03d}.jpg"
        filepath = os.path.join(save_dir, filename)

        # Simpan frame sebagai JPG
        try:
            success = cv2.imwrite(filepath, frame)
            if success:
                self.status_signal.emit(f"Foto tersimpan: {filename}")
                return os.path.abspath(filepath)
            else:
                self.error_signal.emit("Gagal menyimpan foto (cv2.imwrite failed).")
                return ""
        except Exception as e:
            self.error_signal.emit(f"Error saat menyimpan foto: {e}")
            return ""

    def is_active(self) -> bool:
        """
        Periksa apakah kamera sedang aktif dan streaming.
        
        Returns:
            bool: True jika berjalan dan tidak di-pause.
        """
        return self.running and not self.paused

    def change_source(self, new_source):
        """
        Mengubah sumber kamera (misalnya dari index 0 ke link RTSP).
        Jika sedang berjalan, restart otomatis.
        
        Args:
            new_source: Index kamera (int) atau link RTSP (str).
        """
        self.camera_index = new_source
        if self.running:
            self.stop()
            self.wait(2000)
            self.start()

    def __repr__(self) -> str:
        if self.running and not self.paused:
            state = "Streaming"
        elif self.running and self.paused:
            state = "Paused"
        else:
            state = "Stopped"
        return f"CameraThread(index={self.camera_index}, state='{state}')"
