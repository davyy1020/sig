from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QGroupBox, QProgressBar, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.styles import get_button_style, get_progress_bar_style

class SensorPage(QWidget):
    data_saved = pyqtSignal()
    go_back = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sensor = None
        self.form_data = {}
        self.photo_path = ""
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        header = QLabel("Pembacaan Sensor NPK")
        header.setObjectName("title_label")
        main_layout.addWidget(header)
        
        self.sensor_cards = {}
        grid = QGridLayout()
        grid.setSpacing(16)
        
        params = [
            ("Nitrogen", "N", 500, "#00E087", "mg/kg"),
            ("Phosphor", "P", 500, "#00D0FF", "mg/kg"),
            ("Kalium", "K", 500, "#FFD700", "mg/kg"),
            ("pH", "pH", 14, "#FF5E5E", ""),
            ("EC", "EC", 2000, "#00E087", "µS/cm"),
            ("Moisture", "M", 100, "#00D0FF", "%"),
            ("Temperature", "T", 50, "#FFD700", "°C")
        ]
        
        for i, (name, symbol, max_val, color, unit) in enumerate(params):
            card = QFrame()
            card.setObjectName("sensor_card")
            card_layout = QVBoxLayout(card)
            
            title = QLabel(f"{name} ({symbol})")
            title.setObjectName("field_label")
            
            if unit:
                val_label = QLabel(f"0<span style='font-size: 20px; font-weight: 600; color: #94A3B8;'> {unit}</span>")
            else:
                val_label = QLabel("0")
            val_label.setObjectName("stat_value")
            
            prog = QProgressBar()
            prog.setMaximum(max_val)
            prog.setStyleSheet(get_progress_bar_style(color))
            
            card_layout.addWidget(title)
            card_layout.addWidget(val_label)
            card_layout.addWidget(prog)
            
            self.sensor_cards[name.lower()] = {'val': val_label, 'prog': prog, 'unit': unit}
            grid.addWidget(card, i // 4, i % 4)
            
        main_layout.addLayout(grid, 1)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(24)
        
        self.btn_back = QPushButton("📷 Kembali ke Kamera")
        self.btn_back.setStyleSheet(get_button_style('ghost'))
        self.btn_back.setMinimumSize(220, 60)
        self.btn_back.clicked.connect(self.go_back.emit)
        btn_layout.addWidget(self.btn_back)
        
        btn_layout.addStretch()
        
        self.btn_read = QPushButton("🔄 Baca Sensor")
        self.btn_read.setStyleSheet(get_button_style('secondary'))
        self.btn_read.setMinimumSize(200, 60)
        self.btn_read.clicked.connect(self.on_read)
        btn_layout.addWidget(self.btn_read)
        
        self.btn_save = QPushButton("💾 Simpan Data")
        self.btn_save.setStyleSheet(get_button_style('primary'))
        self.btn_save.setMinimumSize(220, 60)
        self.btn_save.clicked.connect(self.on_save)
        btn_layout.addWidget(self.btn_save)
        
        main_layout.addLayout(btn_layout)

    def set_sensor(self, sensor):
        self.sensor = sensor

    def set_form_data(self, data):
        self.form_data = data

    def set_photo_path(self, path):
        self.photo_path = path

    def on_read(self):
        if self.sensor:
            data = self.sensor.read_sensor()
            self.update_display(data)

    def update_display(self, data):
        for k, v in data.items():
            if k in self.sensor_cards:
                unit = self.sensor_cards[k]['unit']
                if unit:
                    self.sensor_cards[k]['val'].setText(f"{v}<span style='font-size: 20px; font-weight: 600; color: #94A3B8;'> {unit}</span>")
                else:
                    self.sensor_cards[k]['val'].setText(str(v))
                self.sensor_cards[k]['prog'].setValue(int(float(v)))

    def on_save(self):
        # 1. Strict Validation of required form fields (deferred validation)
        nama_perusahaan = self.form_data.get('nama_perusahaan', '').strip()
        nama_kebun = self.form_data.get('nama_kebun', '').strip()
        
        if not nama_perusahaan or not nama_kebun:
            QMessageBox.warning(
                self, 
                "Form Belum Lengkap ⚠️", 
                "Nama Perusahaan dan Nama Kebun wajib diisi!\nKami akan mengalihkan Anda kembali ke Form Kebun untuk melengkapinya."
            )
            # Safely navigate to the form tab (index 0) in MainWindow
            if self.window() and hasattr(self.window(), '_navigate_to'):
                self.window()._navigate_to(0)
            return
            
        # 2. Smart Auto-Read sensor data if no reading has been taken yet
        if self.sensor and not self.sensor.last_reading:
            self.on_read()
            
        final_data = self.form_data.copy()
        if self.photo_path:
            final_data['foto_path'] = self.photo_path
            
        if hasattr(self.window(), 'camera_page') and hasattr(self.window().camera_page, 'camera_thread'):
            vid = getattr(self.window().camera_page.camera_thread, 'current_video_path', "")
            if vid:
                final_data['video_path'] = vid

        if self.sensor and self.sensor.last_reading:
            final_data.update(self.sensor.last_reading)
            
        db = self.window().db_handler
        db.insert_inspection(final_data)
        self.data_saved.emit()
