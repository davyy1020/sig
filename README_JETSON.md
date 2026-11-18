# 🚀 DEPLOYMENT & SKRIPSI AUTOMATION GUIDE: JETSON NANO

Panduan lengkap instalasi dan deployment **Sistem Monitoring Kebun Berbasis AI Camera, Sensor NPK 7-in-1, & Gimbal 3-Axis PCA9685** pada **NVIDIA Jetson Nano**.

---

## 📁 Isi Paket Deployment (`sig_jetson_deploy.zip`)
1. **`main.py`** — Entry point Aplikasi Desktop PyQt5.
2. **`ui/`** — Modul Antarmuka (PyQt5 Desktop & Kiosk Web Server Flask).
3. **`camera/`** — Modul kamera OpenCV & Driver Gimbal 3-Axis PCA9685 I2C (`gimbal_control.py`).
4. **`sensor/`** — Modul Driver Sensor NPK 7-in-1 RS485 Modbus RTU (`npk_sensor.py`).
5. **`database/`** — Database Handler SQLite (`db_handler.py`).
6. **`api/`** — Modul HTTP Upload API Server (`api_handler.py`).
7. **`servo_calibration_gui.py`** — Studio Kalibrasi Gimbal Kinematik 3D & 2D Trackpad Touchpad.
8. **`requirements.txt`** — Dependensi Python yang disesuaikan untuk Python 3.6 di Jetson Nano.
9. **`setup_jetson.sh`** — Script installer otomatis untuk I2C, Camera, Serial, & Systemd Service.
10. **`deploy_to_jetson.py`** — Script upload otomatis dari Laptop/PC ke Jetson Nano via SSH.

---

## ⚡ CARA 1: Upload Otomatis dari Laptop via SSH (Disarankan)

Cukup jalankan satu perintah dari terminal laptop (Windows/Linux/Mac):

```bash
python deploy_to_jetson.py <IP_JETSON_NANO> <USERNAME> <PASSWORD>
```
*Contoh:*
```bash
python deploy_to_jetson.py 192.168.1.100 jetson jetson
```
Script akan otomatis mengirim seluruh file, menginstall dependensi, dan mengaktifkan service di Jetson Nano.

---

## 📦 CARA 2: Upload Manual File Single Zip (`sig_jetson_deploy.zip`)

Jika Anda ingin meng-copy file `.zip` langsung menggunakan Flashdisk atau SCP:

1. Copy file **`sig_jetson_deploy.zip`** ke Jetson Nano.
2. Buka terminal di Jetson Nano dan jalankan:
   ```bash
   # Extract zip ke folder ~/sig
   unzip sig_jetson_deploy.zip -d ~/sig
   cd ~/sig

   # Jalankan installer otomatis
   sudo bash setup_jetson.sh
   ```

---

## 🌐 Akses Aplikasi & Layanan
- **Web Kiosk Dashboard:** Open browser di Laptop/HP -> `http://<IP_JETSON_NANO>:5000`
- **Studio Kalibrasi Servo Gimbal (GUI Desktop):**
  ```bash
  python3 servo_calibration_gui.py
  ```
- **Aplikasi Utama Desktop (PyQt5 GUI):**
  ```bash
  python3 main.py
  ```

---

## 🔧 Troubleshooting & Log Sistem
- Cek status service autorun:
  ```bash
  sudo systemctl status sig-kiosk.service
  ```
- Cek log realtime service:
  ```bash
  sudo journalctl -u sig-kiosk.service -f
  ```
- Cek perangkat I2C PCA9685 di Jetson Nano (Port I2C Bus 1):
  ```bash
  sudo i2cdetect -y -r 1
  ```
  *(Alamat PCA9685 default adalah `0x40`)*
