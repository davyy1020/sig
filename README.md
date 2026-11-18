# SIG — Sistem Monitoring & Inspeksi Kebun Kelapa Sawit (IoT, E-Nose & AI Vision)

Sistem terintegrasi berbasis **NVIDIA Jetson Nano**, **ESP32 Multi-Sensor (NPK & Electronic Nose)**, **Arduino Stepper Gimbal**, **Kamera IP TP-Link VIGI Optical Zoom**, dan **AI YOLO Deteksi Jamur Ganoderma** untuk survei kesehatan pohon kelapa sawit di lapangan.

---

## Arsitektur & Fitur Utama

1. **Web Dashboard Kiosk Gateway (`ui/app.py`)**
   - Backend Python Flask & antarmuka touch-screen responsif 4 tahap:
     1. **Dashboard / Form:** Input identitas kebun, blok, pohon fokus, status kesehatan, dan **Visual Mapping Graph Spasial** antar-pohon tetangga (sudut derajat, jarak meter, interaksi sentuhan tajuk daun).
     2. **Kamera Inspeksi:** Live streaming low-latency (GStreamer Hardware Decode `nvv4l2decoder` di Jetson Nano) untuk mode **Normal (TP-Link VIGI)** & **AI Ganoderma Live**, kontrol **Motorized Optical Zoom ONVIF (1x–4x)**, **Stepper Joystick Gimbal**, serta fitur snapshot & rekam video.
     3. **Baca Sensor Real-Time:** Pembacaan 7 parameter tanah NPK (N, P, K, pH, EC, Kelembaban, Suhu) dan 5 array sensor gas E-Nose (MQ-3, MQ-135 Amonia, MQ-138, TGS-2600, TGS-2602).
     4. **Riwayat Inspeksi:** Penyimpanan lokal otomatis ke SQLite (`data.db`) dengan skema auto-migration, filter pencarian, detail modal, ekspor CSV, dan sinkronisasi cloud.

2. **Firmware ESP32 Multi-Sensor (`sensor/esp32_adc2_wifi_continuous_master/`)**
   - Driver RS485 Modbus RTU untuk sensor tanah NPK 7-in-1.
   - Pembacaan ADC2 multi-sensor gas semikonduktor (MQ & TGS).
   - Transmisi kontinu Wi-Fi HTTP POST ke Jetson Nano (`/api/sensor/push`) beserta redundansi Hardware Serial UART.

3. **Kontrol Stepper Gimbal Arduino (`cnc_stepper_control/cnc_stepper_control.ino`)**
   - Kendali 2 sumbu Pan & Tilt (Atas/Bawah & Kiri/Kanan) menggunakan driver stepper & `AccelStepper` via USB Serial 115200 bps dengan safety auto-stop timeout.

4. **Integrasi AI Deteksi Ganoderma**
   - Proxy streaming real-time & snapshot teranotasi dari service model AI TensorRT FP16 (`igano-live` port `8080`).

---

## Struktur Direktori Source Code

```text
sig/
├── main.py                                    # Entry point aplikasi desktop/kiosk
├── requirements.txt                           # Daftar dependensi Python
├── sig-kiosk.service                          # Konfigurasi systemd auto-start Linux/Jetson
├── setup_jetson.sh / setup_fresh_jetson.sh    # Script instalasi environment Jetson Nano
├── gimbal_calibration.json                    # Kalibrasi posisi & batas gimbal
├── api/
│   └── api_handler.py                         # Integrasi sinkronisasi REST API / Cloud
├── camera/
│   ├── camera_handler.py                      # Handler kamera RTSP / USB
│   ├── gimbal_control.py                      # Kontrol gimbal
│   ├── stepper_control.py                     # Komunikasi serial stepper motor
│   ├── stepper_web_bridge.py                  # Bridge web API ke Arduino stepper
│   └── vigi_zoom.py                           # Kontrol Motorized Optical Zoom ONVIF TP-Link VIGI
├── database/
│   ├── db_handler.py                          # SQLite handler + auto-migration kolom NPK & Gas
│   ├── mysql_db_handler.py                    # Opsional handler MySQL
│   └── schema_mysql.sql                       # Skema tabel MySQL
├── sensor/
│   ├── esp32_uart_reader.py                   # Reader serial UART ESP32 di Jetson Nano
│   ├── npk_sensor.py                          # Parser sensor NPK
│   └── esp32_adc2_wifi_continuous_master/
│       └── esp32_adc2_wifi_continuous_master.ino   # Firmware produksi ESP32 (NPK + 5 Gas)
├── cnc_stepper_control/
│   └── cnc_stepper_control.ino                # Firmware produksi Arduino Stepper Gimbal
├── ui/
│   ├── app.py                                 # Server utama Flask Kiosk Gateway (port 5000)
│   ├── templates/index.html                   # Halaman utama antarmuka Kiosk
│   └── static/
│       ├── css/style.css                      # Styling Neo-Brutalism responsif
│       └── js/script.js                       # Logika UI, visual graph, kontrol kamera & sensor
├── web_report/                                # Modul Web Report (Python Flask)
└── web_report_php/                            # Modul Web Report (PHP / MySQL)
```

---

## Cara Instalasi & Menjalankan di Jetson Nano

### 1. Clone Repository & Install Dependensi
```bash
git clone https://github.com/davyy1020/sig.git
cd sig
pip3 install -r requirements.txt
pip3 install flask pyserial onvif-zeep requests
```

### 2. Jalankan Server Kiosk Gateway
```bash
python3 ui/app.py
```
Akses dashboard melalui browser di alamat:
```text
http://<IP_JETSON_NANO>:5000
```

### 3. Mengaktifkan Auto-Start (Systemd Service)
```bash
sudo cp sig-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sig-kiosk.service
```

### 4. Upload Firmware Mikrokontroler
- **ESP32 Sensor Node:** Buka `sensor/esp32_adc2_wifi_continuous_master/esp32_adc2_wifi_continuous_master.ino` di Arduino IDE, sesuaikan Wi-Fi SSID & IP Jetson Nano, lalu upload ke board ESP32.
- **Arduino Stepper Gimbal:** Buka `cnc_stepper_control/cnc_stepper_control.ino` di Arduino IDE (pastikan library `AccelStepper` terpasang), lalu upload ke Arduino Uno/Nano.

---

## Kontributor Teknis
- **Developer & System Integrator:** Davy Wahyu Saputra (`davysaputra1020@gmail.com`)
