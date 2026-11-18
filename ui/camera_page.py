import os
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QSizePolicy, QLineEdit, QFrame,
    QScrollArea, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QImage, QPixmap

from ui.styles import get_button_style

class CameraPage(QWidget):
    photo_captured = pyqtSignal(str)
    go_to_sensor = pyqtSignal()
    go_back = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_thread = None
        self.captured_paths = []
        self._init_ui()
        
        # Apply Neubrutalism style to the entire CameraPage
        self.setStyleSheet("""
            QWidget {
                font-family: 'Space Grotesk', 'Segoe UI', -apple-system, sans-serif;
            }
            
            /* Card Frame / GroupBox Neubrutalism */
            QFrame#card_frame, QGroupBox#capture_card, QGroupBox#control_card, QGroupBox#ptz_card {
                background-color: #1A1A1E;
                border: 3px solid #000000;
                border-radius: 8px;
                margin-top: 0px;
                padding: 16px;
            }
            
            /* Title Labels with Highlight Badge styling */
            QLabel#card_title {
                font-size: 16px;
                font-weight: 900;
                color: #000000;
                background-color: #FFDE4D; /* Neubrutalism Yellow */
                border: 3px solid #000000;
                border-radius: 4px;
                padding: 6px 12px;
            }
            
            /* Secondary Labels */
            QLabel#secondary_label {
                color: #94A3B8;
                font-size: 14px;
            }
            
            /* Input field styling */
            QLineEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 3px solid #000000;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                min-height: 40px;
            }
            QLineEdit:focus {
                background-color: #FFFEEA;
                border: 3px solid #000000;
            }
            
            /* Standard Button Neubrutalism styling */
            QPushButton {
                background-color: #FFDE4D; /* Yellow default */
                color: #000000;
                border-top: 2px solid #000000;
                border-left: 2px solid #000000;
                border-bottom: 6px solid #000000;
                border-right: 6px solid #000000;
                border-radius: 6px;
                font-weight: 900;
                font-size: 15px;
                padding: 10px 16px;
                min-height: 44px;
            }
            QPushButton:hover {
                background-color: #FFEE7C;
            }
            QPushButton:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #E2C23B;
            }
            QPushButton:disabled {
                background-color: #2D3748;
                color: #718096;
                border: 3px solid #1A202C;
            }
            
            /* PTZ Directional Button Styling */
            QPushButton[ptz="true"] {
                background-color: #FFDE4D;
                color: #000000;
                border-top: 2px solid #000000;
                border-left: 2px solid #000000;
                border-bottom: 5px solid #000000;
                border-right: 5px solid #000000;
                border-radius: 6px;
                font-weight: 900;
                font-size: 20px;
                padding: 0px;
            }
            QPushButton[ptz="true"]:hover {
                background-color: #FFEE7C;
            }
            QPushButton[ptz="true"]:pressed {
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-bottom: 2px solid #000000;
                border-right: 2px solid #000000;
                background-color: #E2C23B;
            }
            
            /* PTZ Home Button Styling */
            QPushButton[ptz_home="true"] {
                background-color: #38BDF8;
                color: #000000;
                border-top: 2px solid #000000;
                border-left: 2px solid #000000;
                border-bottom: 5px solid #000000;
                border-right: 5px solid #000000;
                border-radius: 6px;
                font-weight: 900;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton[ptz_home="true"]:hover {
                background-color: #7DD3FC;
            }
            QPushButton[ptz_home="true"]:pressed {
                border-top: 4px solid #000000;
                border-left: 4px solid #000000;
                border-bottom: 2px solid #000000;
                border-right: 2px solid #000000;
                background-color: #0284C7;
            }
            
            /* Color variants for specific buttons using objectNames */
            QPushButton#nb_btn_capture {
                background-color: #00F5D4; /* Bright Teal */
            }
            QPushButton#nb_btn_capture:hover {
                background-color: #5CFCE6;
            }
            QPushButton#nb_btn_capture:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #00C4AA;
            }
            
            QPushButton#nb_btn_start {
                background-color: #FF5E62; /* Coral/Red */
                color: #FFFFFF;
            }
            QPushButton#nb_btn_start:hover {
                background-color: #FF8588;
            }
            QPushButton#nb_btn_start:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #D64246;
            }
            
            QPushButton#nb_btn_pause {
                background-color: #F1F5F9;
                color: #000000;
            }
            QPushButton#nb_btn_pause:hover {
                background-color: #E2E8F0;
            }
            QPushButton#nb_btn_pause:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #CBD5E1;
            }
            
            QPushButton#nb_btn_stop {
                background-color: #EF4444; /* Darker Red */
                color: #FFFFFF;
            }
            QPushButton#nb_btn_stop:hover {
                background-color: #F87171;
            }
            QPushButton#nb_btn_stop:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #DC2626;
            }
            
            QPushButton#nb_btn_set_rtsp {
                background-color: #A78BFA; /* Lavender */
            }
            QPushButton#nb_btn_set_rtsp:hover {
                background-color: #C4B5FD;
            }
            QPushButton#nb_btn_set_rtsp:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #8B5CF6;
            }
            
            QPushButton#nb_btn_back {
                background-color: #E2E8F0;
                color: #000000;
            }
            QPushButton#nb_btn_back:hover {
                background-color: #F1F5F9;
            }
            QPushButton#nb_btn_back:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #CBD5E1;
            }
            
            QPushButton#nb_btn_next {
                background-color: #38BDF8; /* Sky Blue */
                color: #000000;
            }
            QPushButton#nb_btn_next:hover {
                background-color: #7DD3FC;
            }
            QPushButton#nb_btn_next:pressed {
                border-top: 5px solid #000000;
                border-left: 5px solid #000000;
                border-bottom: 3px solid #000000;
                border-right: 3px solid #000000;
                background-color: #0284C7;
            }
        """)

        # Pulsing LIVE/REC indicator timer
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self.toggle_live_pulse)
        self.pulse_visible = True
        self.pulse_timer.start(500)

    def showEvent(self, event):
        super().showEvent(event)
        # Auto-start stream when page is shown
        if self.camera_thread:
            if not self.camera_thread.isRunning():
                self.camera_thread.start()
            elif self.camera_thread.paused:
                self.camera_thread.resume()

    def _init_ui(self):
        # Main layout with defensive padding for small resolutions
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 16, 24, 16)
        main_layout.setSpacing(14)

        # ── Header & Subtitle ──────────────────────────────────────────
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(4)
        
        header = QLabel("Kamera Inspeksi")
        header.setObjectName("title_label")
        header.setStyleSheet("font-size: 28px; font-weight: 800; color: #FFFFFF;")
        
        subtitle = QLabel("Ambil foto kondisi daun atau buah kelapa sawit secara real-time untuk analisis.")
        subtitle.setObjectName("secondary_label")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 15px;")
        
        header_layout.addWidget(header)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header_container)

        # ── Workspace Layout (2 Columns) ────────────────────────────────
        workspace_layout = QHBoxLayout()
        workspace_layout.setSpacing(20)
        main_layout.addLayout(workspace_layout)

        # ── LEFT COLUMN: Camera Stream & Direct Controls (60% width) ─────
        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        # Premium Camera Container (Neubrutalism Card)
        cam_container = QFrame()
        cam_container.setObjectName("card_frame")
        cam_container_layout = QVBoxLayout(cam_container)
        cam_container_layout.setContentsMargins(0, 12, 0, 0)
        cam_container_layout.setSpacing(12)

        # Header layout inside camera container for title and status badges
        cam_header = QHBoxLayout()
        cam_header.setContentsMargins(16, 4, 16, 4)
        
        cam_title = QLabel("🎥 KONEKSI VIDEO LIVE")
        cam_title.setStyleSheet("color: #FFFFFF; font-weight: 800; font-size: 14px;")
        cam_header.addWidget(cam_title)
        cam_header.addStretch()
        
        # Live Badge Overlay
        self.live_badge = QLabel("● LIVE FEED")
        self.live_badge.setStyleSheet("""
            background-color: #00F5D4;
            color: #000000;
            border: 2px solid #000000;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 900;
        """)
        self.live_badge.hide()
        cam_header.addWidget(self.live_badge)

        # Recording Badge Overlay
        self.rec_badge = QLabel("🔴 RECORDING")
        self.rec_badge.setStyleSheet("""
            background-color: #FF5E62;
            color: #FFFFFF;
            border: 2px solid #000000;
            border-radius: 4px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 900;
        """)
        self.rec_badge.hide()
        cam_header.addWidget(self.rec_badge)
        
        cam_container_layout.addLayout(cam_header)

        # Make video_label expand dynamically to fill the container beautifully in 16:9
        self.video_label = QLabel()
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(480, 270)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            background-color: #000000;
            color: #00F5D4;
            font-size: 18px;
            font-weight: 700;
            border: none;
            border-top: 4px solid #000000;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        """)
        
        self.set_placeholder()
        cam_container_layout.addWidget(self.video_label, 1)

        left_column.addWidget(cam_container, 1)
        workspace_layout.addLayout(left_column, 6)

        # ── RIGHT COLUMN: Scrollable Container for controls & gallery (40% width) ────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #FFDE4D;
                border: 2px solid #000000;
                border-radius: 4px;
                min-height: 40px;
            }
            QScrollBar::handle:vertical:hover {
                background: #FFEE7C;
            }
        """)

        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_column = QVBoxLayout(right_widget)
        right_column.setContentsMargins(0, 0, 8, 0) # Breathing room for scrollbar
        right_column.setSpacing(16)

        # Card 1: Galeri Hasil Capture (Neubrutalism Card)
        capture_card = QGroupBox()
        capture_card.setObjectName("capture_card")
        capture_card.setMinimumHeight(170)
        capture_layout = QVBoxLayout(capture_card)
        capture_layout.setContentsMargins(16, 16, 16, 16)
        capture_layout.setSpacing(14)

        capture_title_layout = QHBoxLayout()
        capture_title = QLabel("🖼 Galeri Capture")
        capture_title.setObjectName("card_title")
        
        self.capture_count_label = QLabel("Total: 0")
        self.capture_count_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-weight: 700; background-color: #000000; border: 2px solid #000000; border-radius: 4px; padding: 4px 8px;")
        self.capture_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        capture_title_layout.addWidget(capture_title)
        capture_title_layout.addStretch()
        capture_title_layout.addWidget(self.capture_count_label)
        capture_layout.addLayout(capture_title_layout)

        # Horizontal Scroll Area for Gallery Strip
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
            }
            QScrollBar::handle:horizontal {
                background: #00F5D4;
                border: 2px solid #000000;
                border-radius: 4px;
            }
        """)
        self.scroll_area.setFixedHeight(110)

        # Container for gallery items
        self.gallery_widget = QWidget()
        self.gallery_widget.setStyleSheet("background: transparent;")
        self.gallery_layout = QHBoxLayout(self.gallery_widget)
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_layout.setSpacing(12)
        self.gallery_layout.setAlignment(Qt.AlignLeft)
        self.scroll_area.setWidget(self.gallery_widget)
        
        # Gallery Placeholder Label
        self.placeholder_label = QLabel("Belum ada foto yang diambil")
        self.placeholder_label.setStyleSheet("color: #64748B; font-size: 14px; font-style: italic;")
        self.gallery_layout.addWidget(self.placeholder_label)

        capture_layout.addWidget(self.scroll_area)
        right_column.addWidget(capture_card)

        # Card 2: Kontrol & Sumber Aliran (Neubrutalism Card)
        control_card = QGroupBox()
        control_card.setObjectName("control_card")
        control_layout = QVBoxLayout(control_card)
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(12)
        
        control_title = QLabel("📸 Kontrol & Sumber Kamera")
        control_title.setObjectName("card_title")
        control_layout.addWidget(control_title)

        # Subsection A: Sumber Aliran
        src_input_layout = QHBoxLayout()
        src_input_layout.setSpacing(8)
        self.input_rtsp = QLineEdit()
        self.input_rtsp.setPlaceholderText("Index (0, 1) atau Link RTSP...")
        self.input_rtsp.setFixedHeight(40)
        
        self.btn_set_rtsp = QPushButton("Set Stream")
        self.btn_set_rtsp.setObjectName("nb_btn_set_rtsp")
        self.btn_set_rtsp.setFixedHeight(40)
        self.btn_set_rtsp.setCursor(Qt.PointingHandCursor)
        self.btn_set_rtsp.clicked.connect(self.on_set_rtsp)

        src_input_layout.addWidget(self.input_rtsp, 1)
        src_input_layout.addWidget(self.btn_set_rtsp)
        control_layout.addLayout(src_input_layout)

        # Subsection B: Ambil Foto (Primary Action)
        self.btn_capture = QPushButton("📸 Ambil Foto")
        self.btn_capture.setObjectName("nb_btn_capture")
        self.btn_capture.setFixedHeight(46)
        self.btn_capture.setCursor(Qt.PointingHandCursor)
        self.btn_capture.clicked.connect(self.on_capture)
        control_layout.addWidget(self.btn_capture)
        
        # Subsection C: Kontrol Aliran/Perekaman
        stream_bar = QHBoxLayout()
        stream_bar.setSpacing(6)
        
        self.btn_start = QPushButton("🔴 Record")
        self.btn_start.setObjectName("nb_btn_start")
        self.btn_start.setFixedHeight(44)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.clicked.connect(self.on_start)
        
        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setObjectName("nb_btn_pause")
        self.btn_pause.setFixedHeight(44)
        self.btn_pause.setCursor(Qt.PointingHandCursor)
        self.btn_pause.clicked.connect(self.on_pause)
        
        self.btn_stop = QPushButton("⏹ Stop Rec")
        self.btn_stop.setObjectName("nb_btn_stop")
        self.btn_stop.setFixedHeight(44)
        self.btn_stop.setCursor(Qt.PointingHandCursor)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.on_stop)
        
        stream_bar.addWidget(self.btn_start)
        stream_bar.addWidget(self.btn_pause)
        stream_bar.addWidget(self.btn_stop)
        control_layout.addLayout(stream_bar)
        
        right_column.addWidget(control_card)

        # Card 3: PTZ Controller (Neubrutalism Card)
        ptz_card = QGroupBox()
        ptz_card.setObjectName("ptz_card")
        ptz_layout = QVBoxLayout(ptz_card)
        ptz_layout.setContentsMargins(16, 16, 16, 16)
        ptz_layout.setSpacing(12)
        
        ptz_title = QLabel("🎛 Kontrol Arah Kamera")
        ptz_title.setObjectName("card_title")
        ptz_layout.addWidget(ptz_title)
        
        # Grid of 8 arrows
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        
        # Define buttons
        self.btn_nw = QPushButton("↖")
        self.btn_n = QPushButton("⬆")
        self.btn_ne = QPushButton("↗")
        self.btn_w = QPushButton("⬅")
        self.btn_home = QPushButton("🏠")
        self.btn_e = QPushButton("➡")
        self.btn_sw = QPushButton("↙")
        self.btn_s = QPushButton("⬇")
        self.btn_se = QPushButton("↘")
        
        # Connect signals
        self.btn_nw.clicked.connect(lambda: self.on_ptz("NW"))
        self.btn_n.clicked.connect(lambda: self.on_ptz("N"))
        self.btn_ne.clicked.connect(lambda: self.on_ptz("NE"))
        self.btn_w.clicked.connect(lambda: self.on_ptz("W"))
        self.btn_home.clicked.connect(lambda: self.on_ptz("HOME"))
        self.btn_e.clicked.connect(lambda: self.on_ptz("E"))
        self.btn_sw.clicked.connect(lambda: self.on_ptz("SW"))
        self.btn_s.clicked.connect(lambda: self.on_ptz("S"))
        self.btn_se.clicked.connect(lambda: self.on_ptz("SE"))
        
        # Style buttons with properties
        for btn in [self.btn_nw, self.btn_n, self.btn_ne, self.btn_w, self.btn_e, self.btn_sw, self.btn_s, self.btn_se]:
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFixedSize(54, 54)
            btn.setProperty("ptz", "true")
            
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setFixedSize(54, 54)
        self.btn_home.setProperty("ptz_home", "true")
        
        # Add to grid
        grid_layout.addWidget(self.btn_nw, 0, 0, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_n, 0, 1, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_ne, 0, 2, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_w, 1, 0, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_home, 1, 1, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_e, 1, 2, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_sw, 2, 0, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_s, 2, 1, Qt.AlignCenter)
        grid_layout.addWidget(self.btn_se, 2, 2, Qt.AlignCenter)
        
        ptz_layout.addLayout(grid_layout)
        right_column.addWidget(ptz_card)

        # Spacer to push everything up beautifully
        right_column.addStretch(1)

        # Wrap right panel inside the scroll area
        right_scroll.setWidget(right_widget)
        workspace_layout.addWidget(right_scroll, 4)

        # ── Bottom Navigation Row (Spans Full Page) ──────────────────────
        nav_border = QFrame()
        nav_border.setFrameShape(QFrame.HLine)
        nav_border.setStyleSheet("color: #000000; border-top: 3px solid #000000;")
        main_layout.addWidget(nav_border)

        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 4, 0, 4)

        self.btn_back = QPushButton("📋 Kembali ke Form")
        self.btn_back.setObjectName("nb_btn_back")
        self.btn_back.setCursor(Qt.PointingHandCursor)
        self.btn_back.setFixedHeight(48)
        self.btn_back.clicked.connect(self.go_back.emit)

        self.btn_next = QPushButton("Lanjut ke Sensor 📊")
        self.btn_next.setObjectName("nb_btn_next")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setFixedHeight(48)
        self.btn_next.clicked.connect(self.go_to_sensor.emit)

        nav_layout.addWidget(self.btn_back)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.btn_next)
        
        main_layout.addLayout(nav_layout)

    def set_camera_thread(self, camera_thread):
        self.camera_thread = camera_thread

    def update_frame(self, frame: np.ndarray):
        if frame is None:
            return
            
        # Use contentsRect to get the precise inner size excluding borders/padding
        target_size = self.video_label.contentsRect().size()
        if target_size.width() <= 0 or target_size.height() <= 0:
            return
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        
        # Scale to fit using KeepAspectRatio to show 100% of the photo without cropping
        scaled_pixmap = pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def set_placeholder(self):
        """Resets the video frame viewport to its initial stopped/uninitialized state."""
        self.video_label.clear()
        self.video_label.setText("📷 Kamera belum aktif\nHubungkan dan buka halaman ini")
        self.live_badge.hide()
        self.rec_badge.hide()

    def toggle_live_pulse(self):
        if not self.camera_thread or not self.camera_thread.is_active():
            self.live_badge.hide()
            self.rec_badge.hide()
            return
            
        self.live_badge.show()
        
        # Toggle recording badge state if thread is recording
        if self.camera_thread.recording:
            self.rec_badge.show()
            if self.pulse_visible:
                self.rec_badge.setStyleSheet("""
                    background-color: #FF5E62;
                    color: #FFFFFF;
                    border: 2px solid #000000;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                    font-weight: 900;
                """)
            else:
                self.rec_badge.setStyleSheet("""
                    background-color: rgba(255, 94, 98, 0.2);
                    color: rgba(255, 255, 255, 0.4);
                    border: 2px solid #000000;
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 12px;
                    font-weight: 900;
                """)
        else:
            self.rec_badge.hide()
            
        self.pulse_visible = not self.pulse_visible

    def reset_gallery(self):
        """Clears all captured thumbnails in the scrollable gallery."""
        self.captured_paths = []
        self.capture_count_label.setText("Total: 0")
        
        # Remove all widgets from gallery layout
        for i in reversed(range(self.gallery_layout.count())):
            widget = self.gallery_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        # Re-add placeholder
        self.placeholder_label = QLabel("Belum ada foto yang diambil")
        self.placeholder_label.setStyleSheet("color: #64748B; font-size: 14px; font-style: italic;")
        self.gallery_layout.addWidget(self.placeholder_label)

    def on_set_rtsp(self):
        if not self.camera_thread: return
        source = self.input_rtsp.text().strip()
        if not source: return
        
        if source.isdigit():
            source = int(source)
            
        self.camera_thread.change_source(source)
        if not self.camera_thread.isRunning():
            self.camera_thread.start()

    def on_start(self):
        """Mulai merekam video stream ke file."""
        if not self.camera_thread:
            return
            
        if not self.camera_thread.isRunning():
            self.camera_thread.start()
            QThread.msleep(200)

        # Generate a block name from parent main window context if available
        blok_name = "default"
        if hasattr(self.parent(), 'current_form_data') or (self.window() and hasattr(self.window(), 'current_form_data')):
            win = self.window()
            if hasattr(win, 'current_form_data') and win.current_form_data:
                blok_name = win.current_form_data.get('no_blok', 'default')
                if not blok_name:
                    blok_name = "default"
        
        # Clean name for file system safety
        blok_name = "".join(c for c in blok_name if c.isalnum() or c in ('-', '_')).strip()
        
        videos_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "videos")
        filepath = self.camera_thread.start_recording(videos_dir, blok_name)
        if filepath:
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            if self.window() and hasattr(self.window(), 'status_bar') and self.window().status_bar:
                self.window().status_bar.showMessage(f"🔴 Perekaman video dimulai: {os.path.basename(filepath)}")

    def on_pause(self):
        if self.camera_thread:
            if self.camera_thread.paused:
                self.camera_thread.resume()
            else:
                self.camera_thread.pause()

    def on_stop(self):
        """Hentikan perekaman video stream."""
        if self.camera_thread and self.camera_thread.recording:
            self.camera_thread.stop_recording()
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            if self.window() and hasattr(self.window(), 'status_bar') and self.window().status_bar:
                self.window().status_bar.showMessage("⏹ Perekaman dihentikan, video disimpan.")

    def on_ptz(self, direction):
        """Kirim command arah ke thread kamera."""
        if self.camera_thread:
            self.camera_thread.move_camera(direction)
            if self.window() and hasattr(self.window(), 'status_bar') and self.window().status_bar:
                dir_names = {
                    "NW": "Barat Laut (↖)",
                    "N": "Utara (⬆)",
                    "NE": "Timur Laut (↗)",
                    "W": "Barat (⬅)",
                    "HOME": "Tengah (🏠)",
                    "E": "Timur (➡)",
                    "SW": "Barat Daya (↙)",
                    "S": "Selatan (⬇)",
                    "SE": "Tenggara (↘)"
                }
                self.window().status_bar.showMessage(f"🎛 PTZ: Menggerakkan kamera ke {dir_names.get(direction, direction)}")

    def on_capture(self):
        if self.camera_thread and self.camera_thread.is_active():
            path = self.camera_thread.capture_frame()
            if path:
                # Remove placeholder if it's the first capture
                if len(self.captured_paths) == 0 and hasattr(self, 'placeholder_label'):
                    self.placeholder_label.setParent(None)
                
                self.captured_paths.append(path)
                self.capture_count_label.setText(f"Total: {len(self.captured_paths)}")
                
                # Add gorgeous thumbnail label to gallery strip
                thumb_label = QLabel()
                thumb_label.setFixedSize(120, 90) # Aspect ratio 4:3
                
                pix = QPixmap(path)
                target_size = thumb_label.size()
                scaled_pixmap = pix.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                thumb_label.setPixmap(scaled_pixmap)
                # Neubrutalist borders for the new captures
                thumb_label.setStyleSheet("""
                    border: 3px solid #000000;
                    border-radius: 6px;
                    background-color: #FFFFFF;
                """)
                
                self.gallery_layout.addWidget(thumb_label)
                
                # Emit semicolon-separated paths of all captured photos
                self.photo_captured.emit(";".join(self.captured_paths))
