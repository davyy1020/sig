# 🟢 PANDUAN INTEGRAL SETUP JETSON NANO KOSONGAN (FRESH INSTALL)

Dokumen ini adalah panduan langkah demi langkah (*step-by-step*) untuk menyiapkan **NVIDIA Jetson Nano** baru (fresh/kosongan) sampai aplikasi **Sistem Monitoring Kebun AI Camera, Sensor NPK 7-in-1, & Gimbal 3-Axis PCA9685** siap pakai.

---

## 📋 Tahap 1: Persiapan SD Card & OS Jetson Nano (Jika Belum Ada OS)

Jika Jetson Nano Anda benar-benar baru belum ada SD Card terinstall:
1. Download **JetPack SDK Image** (JetPack 4.6.1 / Ubuntu 18.04 LTS) dari situs resmi NVIDIA:
   [NVIDIA Jetson Nano Developer Kit SD Card Image](https://developer.nvidia.com/embedded/jetpack)
2. Flash file `.img` ke SD Card (minimal 32GB MicroSD Class 10/U3) menggunakan software **BalenaEtcher** atau **Raspberry Pi Imager**.
3. Masukkan MicroSD ke slot Jetson Nano, hubungkan Monitor, Keyboard, dan Daya Power Supply (5V 4A DC Barrel Jack disarankan).
4. Ikuti instruksi di layar monitor Jetson Nano untuk membuat Username dan Password (misal `jetson` / `jetson`).

---

## ⚡ Tahap 2: Transfer Proyek ke Jetson Nano

### Opsi A: Menggunakan Automated Script dari Laptop (Sangat Mudah)
Dari terminal/command prompt di Laptop Anda yang terhubung ke jaringan yang sama dengan Jetson Nano:

```bash
python deploy_to_jetson.py <IP_JETSON_NANO> <USERNAME> <PASSWORD>
```
*Contoh:*
```bash
python deploy_to_jetson.py 192.168.1.100 jetson jetson
```
> **Catatan:** Script ini akan otomatis mentransfer file, membuat SWAP 4GB, menginstall pustaka Python 3.6, mengatur izin I2C/Kamera/Serial, dan menyalakan autorun service.

---

### Opsi B: Transfer File Zip Manual via Flashdisk / SCP
Jika Jetson Nano tidak terhubung ke internet saat pengiriman file:

1. Copy filepaket **`sig_jetson_deploy.zip`** ke Flashdisk.
2. Colok Flashdisk ke Jetson Nano, lalu buka Terminal di Jetson Nano:
   ```bash
   # 1. Ekstrak file zip ke folder ~/sig
   unzip /media/$USER/*/sig_jetson_deploy.zip -d ~/sig
   cd ~/sig

   # 2. Jalankan script installer otomatis untuk Jetson Kosongan
   sudo bash setup_fresh_jetson.sh
   ```

---

## ⚙️ Apa yang Dilakukan oleh Script `setup_fresh_jetson.sh` secara Otomatis?

1. **Membuat SWAP Memory 4GB:** Mencegah Jetson Nano kehabisan RAM (*Out-Of-Memory Crash*) saat pemrosesan OpenCV atau kompilasi pustaka.
2. **Menginstall Pustaka Sistem:** `i2c-tools`, `gstreamer`, `libgl1-mesa-glx`, `python3-pip`, `build-essential`.
3. **Mengaktifkan Hardware I2C Bus 1 & Udev Rules:**
   - Membuka akses pin `SDA/SCL` I2C Bus 1 (Header Pin 3 & 5) tanpa butuh `sudo`.
   - Membuka akses kamera USB/CSI (`/dev/video*`).
   - Membuka akses modul USB-to-RS485 (`/dev/ttyUSB0`) untuk sensor NPK.
4. **Menginstall Dependensi Python 3.6:** `Flask`, `PyQt5`, `opencv-python-headless`, `numpy`, `Pillow`, `smbus2`, `pyserial`, `requests`.
5. **Membuat Service Auto-Run Systemd (`sig-kiosk.service`):**
   Aplikasi dan Web Server akan otomatis berjalan di port 5000 begitu Jetson Nano dinyalakan (*power-on*).

---

## 🔌 Skema Pin Hardware di Jetson Nano

| Komponen | Koneksi di Jetson Nano | Keterangan |
| :--- | :--- | :--- |
| **Driver PCA9685 Servo Gimbal** | Pin 3 (SDA), Pin 5 (SCL), Pin 2/4 (5V), Pin 6 (GND) | Mengendalikan Servo 1 (Pan), Servo 2 (Tilt), Servo 3 (Roll) |
| **Sensor NPK NiuBoL 7-in-1** | Port USB (Modul USB to RS485 converter `/dev/ttyUSB0`) | Jalur komunikasi Modbus RTU RS485 |
| **Kamera Inspeksi** | Port USB (`/dev/video0`) ATAU IP Camera (RTSP Stream) | Pengambilan foto daun/buah kelapa sawit |

---

## 🔍 Cara Verifikasi & Monitoring Perangkat

- **Akses Dashboard Web:** Buka browser di Laptop/HP -> `http://<IP_JETSON_NANO>:5000`
- **Uji Deteksi Gimbal PCA9685 di I2C:**
  ```bash
  sudo i2cdetect -y -r 1
  ```
  *(Pastikan angka `40` muncul pada tabel grid)*

- **Buka Studio Kalibrasi Servo Gimbal 3D / 2D Trackpad (Desktop GUI):**
  ```bash
  cd ~/sig
  python3 servo_calibration_gui.py
  ```

- **Buka Aplikasi Utama Desktop PyQt5:**
  ```bash
  cd ~/sig
  python3 main.py
  ```

- **Cek Log Service Realtime:**
  ```bash
  sudo journalctl -u sig-kiosk.service -f
  ```
