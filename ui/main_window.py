import os
import sys
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QStatusBar, QSizePolicy,
    QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon

from ui.form_page import FormPage
from ui.camera_page import CameraPage
from ui.sensor_page import SensorPage
from ui.data_page import DataPage
from ui.styles import get_button_style

from database.db_handler import DatabaseHandler, get_db_handler
from sensor.npk_sensor import DummyNPKSensor
from camera.camera_handler import CameraThread
from api.api_handler import APIHandler


class MainWindow(QMainWindow):
    PAGE_FORM = 0
    PAGE_CAMERA = 1
    PAGE_SENSOR = 2
    PAGE_DATA = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🌿 Sistem Monitoring Kebun")
        self.setMinimumSize(1100, 750)
        self.resize(1280, 800)

        # ── Initialize Backend ──────────────────────────────────────────
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if not os.path.basename(project_root):
            project_root = os.path.dirname(os.path.abspath(__file__))

        self.images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        os.makedirs(self.images_dir, exist_ok=True)

        # Inisialisasi Database Handler (MySQL / SQLite)
        db_type = os.environ.get("DB_TYPE", "sqlite")
        db_host = os.environ.get("MYSQL_HOST", "localhost")
        db_port = int(os.environ.get("MYSQL_PORT", 3306))
        db_user = os.environ.get("MYSQL_USER", "root")
        db_pass = os.environ.get("MYSQL_PASSWORD", "")
        db_name = os.environ.get("MYSQL_DATABASE", "sig_monitoring")

        self.db_handler = get_db_handler(
            db_type=db_type,
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_pass,
            database=db_name,
        )

        self.sensor = DummyNPKSensor()
        # Inisialisasi Kamera (Default: TP-Link VIGI RTSP Stream)
        default_cam = "rtsp://admin:sigma123@192.168.136.108:554/stream1"
        cam_source = os.environ.get("CAMERA_SOURCE", os.environ.get("CAMERA_RTSP_URL", default_cam))
        self.camera_thread = CameraThread(camera_index=cam_source)
        self.api_handler = APIHandler()

        self.current_form_data = {}
        self.current_photo_path = ""

        # ── Build UI ────────────────────────────────────────────────────
        self._init_ui()
        self._connect_signals()
        self._start_status_timer()
        
        # Start the camera thread on boot
        if self.camera_thread:
            self.camera_thread.start()

    def _init_ui(self):
        central = QWidget()
        central.setObjectName("central_widget")
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: rgba(6, 10, 20, 0.8); border-bottom: 1.5px solid rgba(0, 245, 212, 0.2);")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        logo_label = QLabel("🌿")
        logo_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(logo_label)

        app_title = QLabel("Sistem Monitoring Kebun")
        app_title.setObjectName("title_label")
        header_layout.addWidget(app_title)
        header_layout.addStretch()

        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-weight: 700; font-size: 18px; color: #94A3B8;")
        header_layout.addWidget(self.time_label)

        root_layout.addWidget(header)

        # ── Initialize & Add Step progress bar ────────────────────────
        self._init_step_bar()
        root_layout.addWidget(self.step_bar_frame)

        # ── Stack Container with side padding ──────────────────────────
        stack_container = QWidget()
        stack_layout = QVBoxLayout(stack_container)
        stack_layout.setContentsMargins(24, 24, 24, 24)
        stack_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.form_page = FormPage()
        self.camera_page = CameraPage()
        self.sensor_page = SensorPage()
        self.data_page = DataPage()

        self.stack.addWidget(self.form_page)
        self.stack.addWidget(self.camera_page)
        self.stack.addWidget(self.sensor_page)
        self.stack.addWidget(self.data_page)

        stack_layout.addWidget(self.stack)
        root_layout.addWidget(stack_container, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_db_label = QLabel()
        self.status_cam_label = QLabel()
        self.status_sensor_label = QLabel()

        self.status_bar.addPermanentWidget(self.status_db_label)
        self.status_bar.addPermanentWidget(self.status_cam_label)
        self.status_bar.addPermanentWidget(self.status_sensor_label)

        self._navigate_to(self.PAGE_FORM)
        self._setup_pages()

    def _init_step_bar(self):
        self.step_bar_frame = QFrame()
        self.step_bar_frame.setFixedHeight(84)
        self.step_bar_frame.setStyleSheet("background-color: rgba(4, 6, 12, 0.5); border-bottom: 1.5px solid rgba(0, 245, 212, 0.12);")
        layout = QHBoxLayout(self.step_bar_frame)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(12)
        
        self.step_labels = []
        steps = [
            "📝 Form Kebun",
            "📷 Ambil Foto",
            "📊 Baca Sensor",
            "📤 Riwayat & Upload"
        ]
        
        layout.addStretch()
        for i, name in enumerate(steps):
            if i > 0:
                arrow = QLabel(" ➔ ")
                arrow.setStyleSheet("color: #475569; font-weight: bold; font-size: 18px;")
                layout.addWidget(arrow)
                
            btn = QPushButton(name)
            btn.setMinimumSize(QSize(230, 46))
            btn.setCursor(Qt.PointingHandCursor)
            # Use default parameter value binding for lambda
            btn.clicked.connect(lambda checked, idx=i: self._navigate_to(idx))
            layout.addWidget(btn)
            self.step_labels.append(btn)
        layout.addStretch()

    def _update_step_indicator(self, page_idx):
        for i, btn in enumerate(self.step_labels):
            if i == page_idx:
                # Active step (Vibrant Teal-Green Gradient)
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00F5D4, stop:1 #10B981);
                        color: #04080F;
                        border: none;
                        border-radius: 23px;
                        padding: 8px 20px;
                        font-weight: 700;
                        font-size: 17px;
                        min-height: 46px;
                    }
                """)
            elif i < page_idx:
                # Completed step (Electric Neon Cyan glow glass pill)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(0, 245, 212, 0.08);
                        color: #00F5D4;
                        border: 1.5px solid rgba(0, 245, 212, 0.6);
                        border-radius: 23px;
                        padding: 8px 20px;
                        font-weight: 700;
                        font-size: 17px;
                        min-height: 46px;
                    }
                    QPushButton:hover {
                        background-color: rgba(0, 245, 212, 0.15);
                        border-color: #00F5D4;
                    }
                """)
            else:
                # Upcoming step (Sleek Dark Navy glass pill)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(13, 21, 38, 0.6);
                        color: #64748B;
                        border: 1px solid rgba(255, 255, 255, 0.08);
                        border-radius: 23px;
                        padding: 8px 20px;
                        font-weight: 600;
                        font-size: 17px;
                        min-height: 46px;
                    }
                    QPushButton:hover {
                        background-color: rgba(255, 255, 255, 0.05);
                        color: #F1F5F9;
                        border-color: rgba(255, 255, 255, 0.15);
                    }
                """)

    def _setup_pages(self):
        self.camera_page.set_camera_thread(self.camera_thread)
        self.camera_thread.frame_signal.connect(self.camera_page.update_frame)
        self.camera_thread.error_signal.connect(self._on_camera_error)
        self.camera_thread.status_signal.connect(self._on_camera_status)
        self.sensor_page.set_sensor(self.sensor)
        self.data_page.set_database(self.db_handler)
        self.data_page.set_api_handler(self.api_handler)

    def _connect_signals(self):
        self.form_page.form_completed.connect(self._on_form_completed)
        self.camera_page.photo_captured.connect(self._on_photo_captured)
        self.camera_page.go_to_sensor.connect(self._on_go_to_sensor)
        self.sensor_page.data_saved.connect(self._on_data_saved)
        
        # Sequential Wizard Navigation signals
        self.camera_page.go_back.connect(lambda: self._navigate_to(self.PAGE_FORM))
        self.sensor_page.go_back.connect(lambda: self._navigate_to(self.PAGE_CAMERA))
        self.data_page.start_new_inspection.connect(self.show_form_page)

    def _on_form_completed(self, data: dict):
        self.current_form_data = data
        self.sensor_page.set_form_data(data)
        self._navigate_to(self.PAGE_CAMERA)
        self.status_bar.showMessage("✅ Form selesai — silakan ambil foto", 3000)

    def _on_photo_captured(self, path: str):
        self.current_photo_path = path
        self.sensor_page.set_photo_path(path)
        self.status_bar.showMessage(f"📸 Foto tersimpan: {os.path.basename(path)}", 3000)

    def _on_go_to_sensor(self):
        self._navigate_to(self.PAGE_SENSOR)

    def _on_data_saved(self):
        self.data_page.refresh_table()
        self.current_form_data = {}
        self.current_photo_path = ""
        self.form_page.reset_form()
        self.camera_page.reset_gallery()
        self.status_bar.showMessage("✅ Data berhasil disimpan!", 3000)
        self._navigate_to(self.PAGE_DATA)

    def _on_camera_error(self, msg: str):
        QMessageBox.warning(self, "⚠️ Camera Error", msg)

    def _on_camera_status(self, status: str):
        pass

    def _navigate_to(self, page_idx: int):
        # Optimize CPU by pausing camera stream when leaving camera page
        if self.stack.currentIndex() == self.PAGE_CAMERA and page_idx != self.PAGE_CAMERA:
            if self.camera_thread and self.camera_thread.isRunning() and not self.camera_thread.paused:
                self.camera_thread.pause()

        self.stack.setCurrentIndex(page_idx)
        self._update_step_indicator(page_idx)
        if page_idx == self.PAGE_DATA:
            self.data_page.refresh_table()
        elif page_idx == self.PAGE_CAMERA:
            if self.camera_thread:
                # Auto-start or auto-resume when entering the camera page
                if not self.camera_thread.isRunning():
                    self.camera_thread.start()
                elif self.camera_thread.paused:
                    self.camera_thread.resume()

    def show_form_page(self):
        self.form_page.reset_form()
        self.camera_page.reset_gallery()
        self.current_form_data = {}
        self.current_photo_path = ""
        self._navigate_to(self.PAGE_FORM)

    def _start_status_timer(self):
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)
        self._update_status()

    def _update_status(self):
        now = datetime.now()
        self.time_label.setText(f"📅 {now.strftime('%d/%m/%Y')}  ⏰ {now.strftime('%H:%M:%S')}")
        try:
            count = self.db_handler.get_record_count()
            pending = self.db_handler.get_pending_count()
            self.status_db_label.setText(f"💾 DB: {count} data ({pending} pending)")
        except Exception:
            self.status_db_label.setText("💾 DB: Error")
            
        if self.camera_thread.is_active():
            self.status_cam_label.setText("📷 Camera: Streaming")
        elif self.camera_thread.running and self.camera_thread.paused:
            self.status_cam_label.setText("📷 Camera: Paused")
        else:
            self.status_cam_label.setText("📷 Camera: Ready")
            
        self.status_sensor_label.setText(f"🔌 Sensor: {self.sensor.get_status()}")

    def closeEvent(self, event):
        if self.camera_thread.isRunning():
            self.camera_thread.stop()
            self.camera_thread.wait(2000)
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        self.sensor.disconnect()
        event.accept()
