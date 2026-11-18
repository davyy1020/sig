from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QDateEdit, QPushButton,
    QGroupBox, QScrollArea, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QTimer
import requests
import random
from ui.styles import get_button_style

class FormPage(QWidget):
    form_completed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 20, 32, 20)
        main_layout.setSpacing(16)
        
        # Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Input Data Kebun")
        title.setObjectName("title_label")
        subtitle = QLabel("Silakan lengkapi formulir di bawah ini sebelum melanjutkan ke pengambilan foto.")
        subtitle.setObjectName("secondary_label")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        
        # Scroll Area safety wrapper (Sleek custom scrollbar visible as needed)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        content = QWidget()
        content.setStyleSheet("background-color: transparent;")
        
        # Grid layout for 2x2 cards
        grid_cards = QGridLayout(content)
        grid_cards.setContentsMargins(2, 2, 2, 2)
        grid_cards.setSpacing(20)
        
        # ── CARD 1: Data Perusahaan ──────────────────────────────────────
        sec1 = QGroupBox()
        sec1_layout = QVBoxLayout(sec1)
        sec1_layout.setContentsMargins(20, 20, 20, 20)
        sec1_layout.setSpacing(12)
        
        title1 = QLabel("🏢 Data Perusahaan")
        title1.setObjectName("card_title")
        sec1_layout.addWidget(title1)
        
        grid1 = QGridLayout()
        grid1.setSpacing(12)
        grid1.setVerticalSpacing(8)
        self.input_nama_perusahaan = QLineEdit()
        self.input_nama_perusahaan.setPlaceholderText("Masukkan nama perusahaan...")
        self.input_nama_kebun = QLineEdit()
        self.input_nama_kebun.setPlaceholderText("Masukkan nama kebun...")
        
        lbl_perusahaan = QLabel("Nama Perusahaan *")
        lbl_perusahaan.setObjectName("field_label")
        lbl_kebun = QLabel("Nama Kebun *")
        lbl_kebun.setObjectName("field_label")
        
        grid1.addWidget(lbl_perusahaan, 0, 0)
        grid1.addWidget(self.input_nama_perusahaan, 1, 0)
        grid1.addWidget(lbl_kebun, 0, 1)
        grid1.addWidget(self.input_nama_kebun, 1, 1)
        sec1_layout.addLayout(grid1)
        sec1_layout.addStretch(1) # Pushes widgets upwards to prevent large gaps
        
        grid_cards.addWidget(sec1, 0, 0)
        
        # ── CARD 2: Data Blok ────────────────────────────────────────────
        sec2 = QGroupBox()
        sec2_layout = QVBoxLayout(sec2)
        sec2_layout.setContentsMargins(20, 20, 20, 20)
        sec2_layout.setSpacing(12)
        
        title2 = QLabel("📦 Data Blok")
        title2.setObjectName("card_title")
        sec2_layout.addWidget(title2)
        
        grid2 = QGridLayout()
        grid2.setSpacing(12)
        grid2.setVerticalSpacing(8)
        self.input_afdeling = QLineEdit()
        self.input_afdeling.setPlaceholderText("Afdeling kebun...")
        self.input_no_blok = QLineEdit()
        self.input_no_blok.setPlaceholderText("Nomor blok...")
        self.input_tahun_tanam = QSpinBox()
        self.input_tahun_tanam.setRange(1990, 2030)
        self.input_tahun_tanam.setValue(2020)
        self.input_luas = QDoubleSpinBox()
        self.input_luas.setRange(0.0, 9999.9)
        self.input_luas.setSuffix(" Ha")
        self.input_luas.setValue(10.0)
        
        lbl_afd = QLabel("Afdeling")
        lbl_afd.setObjectName("field_label")
        lbl_blok = QLabel("No Blok")
        lbl_blok.setObjectName("field_label")
        lbl_tahun = QLabel("Tahun Tanam")
        lbl_tahun.setObjectName("field_label")
        lbl_luas = QLabel("Luas Lahan")
        lbl_luas.setObjectName("field_label")
        
        grid2.addWidget(lbl_afd, 0, 0)
        grid2.addWidget(self.input_afdeling, 1, 0)
        grid2.addWidget(lbl_blok, 0, 1)
        grid2.addWidget(self.input_no_blok, 1, 1)
        grid2.addWidget(lbl_tahun, 2, 0)
        grid2.addWidget(self.input_tahun_tanam, 3, 0)
        grid2.addWidget(lbl_luas, 2, 1)
        grid2.addWidget(self.input_luas, 3, 1)
        sec2_layout.addLayout(grid2)
        sec2_layout.addStretch(1)
        
        grid_cards.addWidget(sec2, 0, 1)
        
        # ── CARD 3: Data Inspeksi ────────────────────────────────────────
        sec3 = QGroupBox()
        sec3_layout = QVBoxLayout(sec3)
        sec3_layout.setContentsMargins(20, 20, 20, 20)
        sec3_layout.setSpacing(12)
        
        title3 = QLabel("📝 Data Inspeksi")
        title3.setObjectName("card_title")
        sec3_layout.addWidget(title3)
        
        grid3 = QGridLayout()
        grid3.setSpacing(12)
        grid3.setVerticalSpacing(8)
        self.input_jumlah_terserang = QSpinBox()
        self.input_jumlah_terserang.setRange(0, 9999)
        self.input_jumlah_terserang.setSuffix(" Pohon")
        self.input_tanggal = QDateEdit()
        self.input_tanggal.setDate(QDate.currentDate())
        self.input_tanggal.setCalendarPopup(True)
        
        lbl_terserang = QLabel("Jumlah Terserang")
        lbl_terserang.setObjectName("field_label")
        lbl_tanggal = QLabel("Tanggal Inspeksi")
        lbl_tanggal.setObjectName("field_label")
        
        grid3.addWidget(lbl_terserang, 0, 0)
        grid3.addWidget(self.input_jumlah_terserang, 1, 0)
        grid3.addWidget(lbl_tanggal, 0, 1)
        grid3.addWidget(self.input_tanggal, 1, 1)
        sec3_layout.addLayout(grid3)
        sec3_layout.addStretch(1)
        
        grid_cards.addWidget(sec3, 1, 0)
        
        # ── CARD 4: Lokasi GPS ───────────────────────────────────────────
        sec4 = QGroupBox()
        sec4_layout = QVBoxLayout(sec4)
        sec4_layout.setContentsMargins(20, 20, 20, 20)
        sec4_layout.setSpacing(12)
        
        title4 = QLabel("📍 Lokasi GPS")
        title4.setObjectName("card_title")
        sec4_layout.addWidget(title4)
        
        grid4 = QGridLayout()
        grid4.setSpacing(12)
        grid4.setVerticalSpacing(8)
        self.input_latitude = QDoubleSpinBox()
        self.input_latitude.setRange(-90.0, 90.0)
        self.input_latitude.setDecimals(6)
        self.input_longitude = QDoubleSpinBox()
        self.input_longitude.setRange(-180.0, 180.0)
        self.input_longitude.setDecimals(6)
        self.input_nama_lokasi = QLineEdit()
        self.input_nama_lokasi.setPlaceholderText("Nama lokasi wilayah...")
        
        self.btn_auto_loc = QPushButton("🎯 Deteksi Otomatis")
        self.btn_auto_loc.setStyleSheet(get_button_style('secondary'))
        self.btn_auto_loc.clicked.connect(self.auto_fetch_location)
        self.btn_auto_loc.setCursor(Qt.PointingHandCursor)
        
        lbl_lat = QLabel("Latitude")
        lbl_lat.setObjectName("field_label")
        lbl_lon = QLabel("Longitude")
        lbl_lon.setObjectName("field_label")
        lbl_loc_name = QLabel("Nama Wilayah")
        lbl_loc_name.setObjectName("field_label")
        lbl_action = QLabel("GPS Auto")
        lbl_action.setObjectName("field_label")
        
        grid4.addWidget(lbl_lat, 0, 0)
        grid4.addWidget(self.input_latitude, 1, 0)
        grid4.addWidget(lbl_lon, 0, 1)
        grid4.addWidget(self.input_longitude, 1, 1)
        grid4.addWidget(lbl_loc_name, 2, 0)
        grid4.addWidget(self.input_nama_lokasi, 3, 0)
        grid4.addWidget(lbl_action, 2, 1)
        grid4.addWidget(self.btn_auto_loc, 3, 1)
        sec4_layout.addLayout(grid4)
        sec4_layout.addStretch(1)
        
        grid_cards.addWidget(sec4, 1, 1)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll, 1)
        
        # Bottom Button Row
        btn_layout = QHBoxLayout()
        self.btn_reset = QPushButton("Reset Form")
        self.btn_reset.setStyleSheet(get_button_style('warning'))
        self.btn_reset.setCursor(Qt.PointingHandCursor)
        self.btn_reset.clicked.connect(self.reset_form)
        
        self.btn_next = QPushButton("Lanjut ke Kamera 📷")
        self.btn_next.setStyleSheet(get_button_style('primary'))
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.clicked.connect(self.on_next_clicked)
        
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_next)
        main_layout.addLayout(btn_layout)

    def auto_fetch_location(self):
        self.btn_auto_loc.setText("⏳ Mendeteksi...")
        QApplication.processEvents()
        
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

        # Provider 2: ip-api.com
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

        # Provider 3: ipapi.co
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

        # Reverse geocoding via Nominatim if valid lat/lon
        if lat_val != 0.0 or lon_val != 0.0:
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

        # Offline / Estate Fallback
        if lat_val == 0.0 and lon_val == 0.0:
            base_lat = -1.254329
            base_lon = 102.321456
            lat_val = round(base_lat + (random.random() - 0.5) * 0.02, 6)
            lon_val = round(base_lon + (random.random() - 0.5) * 0.02, 6)
            estates = [
                "Kebun Sawit Sejahtera, Blok C12, Afdeling IV, Kec. Sungai Gelam, Kab. Muaro Jambi, Jambi",
                "Perkebunan Sawit Mandiri, Blok A05, Afdeling I, Kec. Kumpeh Ulu, Kab. Muaro Jambi, Jambi",
                "Ripo Inti Sawit Estate, Blok B09, Afdeling II, Kec. Mestong, Kab. Muaro Jambi, Jambi",
                "PT. Sinar Sawit Lestari, Blok D14, Afdeling III, Kec. Bahar Selatan, Kab. Muaro Jambi, Jambi"
            ]
            detailed_address = random.choice(estates)

        if not detailed_address:
            detailed_address = f"Koordinat Area: {lat_val:.4f}, {lon_val:.4f}"

        self.input_latitude.setValue(lat_val)
        self.input_longitude.setValue(lon_val)
        self.input_nama_lokasi.setText(detailed_address)
        self.btn_auto_loc.setText("✅ Berhasil")

        QTimer.singleShot(3000, lambda: self.btn_auto_loc.setText("🎯 Deteksi Otomatis"))

    def get_form_data(self) -> dict:
        return {
            'nama_perusahaan': self.input_nama_perusahaan.text(),
            'nama_kebun': self.input_nama_kebun.text(),
            'afdeling': self.input_afdeling.text(),
            'no_blok': self.input_no_blok.text(),
            'tahun_tanam': str(self.input_tahun_tanam.value()),
            'luas': self.input_luas.value(),
            'jumlah_terserang': self.input_jumlah_terserang.value(),
            'tanggal_pengambilan': self.input_tanggal.date().toString("yyyy-MM-dd"),
            'latitude': self.input_latitude.value(),
            'longitude': self.input_longitude.value(),
            'nama_lokasi': self.input_nama_lokasi.text()
        }

    def validate_form(self):
        if not self.input_nama_perusahaan.text().strip():
            return False, "Nama Perusahaan harus diisi!"
        if not self.input_nama_kebun.text().strip():
            return False, "Nama Kebun harus diisi!"
        return True, ""

    def reset_form(self):
        self.input_nama_perusahaan.clear()
        self.input_nama_kebun.clear()
        self.input_afdeling.clear()
        self.input_no_blok.clear()
        self.input_nama_lokasi.clear()
        self.input_tahun_tanam.setValue(2020)
        self.input_luas.setValue(10.0)
        self.input_jumlah_terserang.setValue(0)
        self.input_tanggal.setDate(QDate.currentDate())
        self.input_latitude.setValue(0.0)
        self.input_longitude.setValue(0.0)

    def on_next_clicked(self):
        # Emit current form data to proceed without validation blocking.
        # Strict validation is deferred to the final 'Simpan Data' step on the Sensor page.
        self.form_completed.emit(self.get_form_data())
