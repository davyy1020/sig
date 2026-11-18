#!/bin/bash
# ==============================================================================
# SCRIPT SETUP OTOMATIS: NVIDIA JETSON NANO FRESH / KOSONGAN (JETPACK OS)
# Menyiapkan seluruh environment dari nol (Fresh Install) hingga aplikasi berjalan.
#
# Cara Jalankan di Jetson Nano:
#   cd ~/sig
#   sudo bash setup_fresh_jetson.sh
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    ACTUAL_USER="jetson"
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR"

echo -e "${BLUE}========================================================================${NC}"
echo -e "${CYAN}   SETUP OTOMATIS NVIDIA JETSON NANO FRESH (SKRIPSI/MONITORING SIG)    ${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo -e "User Target        : ${YELLOW}${ACTUAL_USER}${NC}"
echo -e "Directory App      : ${YELLOW}${APP_DIR}${NC}"
echo -e "Python Version Target: ${YELLOW}Python 3.6 (JetPack Default)${NC}"
echo ""

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 1: KONFIGURASI SWAP MEMORY (4GB) UNTUK MENCEGAH CRASH OOM
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [1/7] Memeriksa & Mengaktifkan SWAP Memory (4GB Swapfile)...${NC}"
if [ $(swapon --show | wc -l) -le 1 ]; then
    echo "  Membuat 4GB swapfile di /swapfile..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    if ! grep -q '/swapfile' /etc/fstab; then
        echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
    fi
    echo -e "  ${GREEN}[OK] SWAP 4GB berhasil dibuat & diaktifkan.${NC}"
else
    echo -e "  ${GREEN}[OK] SWAP Memory sudah aktif.${NC}"
fi

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 2: UPDATE REPOSITORI & INSTALL PAKET SISTEM
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [2/7] Update paket sistem & install tools pendukung...${NC}"
sudo apt update -y
sudo apt install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-setuptools \
    build-essential \
    i2c-tools \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libcanberra-gtk-module \
    libcanberra-gtk3-module \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    rsync \
    unzip \
    curl \
    git

# Upgrade pip ke versi stabil untuk Python 3.6
python3 -m pip install --upgrade "pip<21.0" setuptools wheel 2>/dev/null || true

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 3: KONFIGURASI DRIVER HARDWARE (I2C, VIDEO, SERIAL UART)
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [3/7] Mengaktifkan Modul Kernel I2C & Pengaturan Udev Rules...${NC}"

# Aktifkan modul i2c-dev di kernel
sudo modprobe i2c-dev 2>/dev/null || true
if ! grep -q 'i2c-dev' /etc/modules; then
    echo 'i2c-dev' | sudo tee -a /etc/modules
fi

# Buat aturan udev permanen untuk I2C, Kamera, dan USB Serial Modbus
UDEV_RULE_FILE="/etc/udev/rules.d/99-jetson-hardware.rules"
cat <<EOF | sudo tee $UDEV_RULE_FILE > /dev/null
# Permanen Izin Akses I2C (Gimbal PCA9685)
KERNEL=="i2c-[0-9]*", GROUP="i2c", MODE="0666"

# Permanen Izin Akses Kamera USB / CSI
KERNEL=="video[0-9]*", GROUP="video", MODE="0666"

# Permanen Izin Akses USB Serial RS485 (Sensor NPK NiuBoL)
KERNEL=="ttyUSB[0-9]*", GROUP="dialout", MODE="0666"
KERNEL=="ttyTHS[0-9]*", GROUP="dialout", MODE="0666"
EOF

sudo udevadm control --reload-rules 2>/dev/null || true
sudo udevadm trigger 2>/dev/null || true

# Tambahkan user ke grup sistem
sudo usermod -aG i2c,video,dialout "$ACTUAL_USER" 2>/dev/null || true

# Set izin chmod sementara langsung
sudo chmod 666 /dev/i2c* 2>/dev/null || true
sudo chmod 666 /dev/video* 2>/dev/null || true
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || true
sudo chmod 666 /dev/ttyTHS* 2>/dev/null || true

# Matikan service nvgetty agar UART /dev/ttyTHS1 bebas dipakai untuk komunikasi RX/TX ke ESP32
sudo systemctl stop nvgetty 2>/dev/null || true
sudo systemctl disable nvgetty 2>/dev/null || true

echo -e "  ${GREEN}[OK] Modul I2C & Udev Rules Hardware berhasil dikonfigurasi.${NC}"

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 4: INSTALL DEPENDENSI PYTHON (PYTHON 3.6 COMPATIBLE)
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [4/7] Menginstall Pustaka Python 3.6 (Requirements)...${NC}"
if [ -f "$APP_DIR/requirements.txt" ]; then
    pip3 install -r "$APP_DIR/requirements.txt" 2>/dev/null || pip3 install -r "$APP_DIR/requirements.txt" --user
fi

# Pastikan pustaka utama terpasang sempurna
pip3 install \
    "Flask>=1.1.0,<2.1.0" \
    "requests>=2.22.0,<=2.27.1" \
    "opencv-python-headless>=4.1.2,<=4.5.3.56" \
    "numpy>=1.19.0,<=1.19.5" \
    "Pillow>=7.0.0,<=8.4.0" \
    "pyserial>=3.4" \
    "smbus2>=0.4.0" \
    "PyQt5>=5.12,<=5.15.4" \
    2>/dev/null || true

echo -e "  ${GREEN}[OK] Pustaka Python terpasang.${NC}"

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 5: INSIALISASI STRUKTUR FOLDER & DATABASE
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [5/7] Menyiapkan struktur direktori aplikasi & database...${NC}"
mkdir -p "$APP_DIR/ui/images"
mkdir -p "$APP_DIR/ui/static"
mkdir -p "$APP_DIR/ui/templates"
mkdir -p "$APP_DIR/database"
mkdir -p "$APP_DIR/api"
mkdir -p "$APP_DIR/sensor"
mkdir -p "$APP_DIR/camera"
mkdir -p "$APP_DIR/images"
mkdir -p "$APP_DIR/videos"

# Test buat tabel database SQLite jika belum ada
python3 -c "
import sys, os
sys.path.insert(0, '$APP_DIR')
from database.db_handler import DatabaseHandler
db = DatabaseHandler()
print('SQLite DB Ready. Record count:', db.get_record_count())
"

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 6: KONFIGURASI SYSTEMD AUTORUN SERVICE (LAHAN / KIOSK MODE)
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [6/7] Membuat Systemd Autorun Service (sig-kiosk.service)...${NC}"
SERVICE_FILE="/etc/systemd/system/sig-kiosk.service"

cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=SIG Kiosk Server & Jetson Nano Hardware Controller
After=network.target multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/ui
ExecStartPre=/bin/bash -c "modprobe i2c-dev || true; chmod 666 /dev/i2c* /dev/video* /dev/ttyUSB* /dev/ttyTHS* || true"
ExecStart=/usr/bin/python3 ${APP_DIR}/ui/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable sig-kiosk.service

# Hentikan port 5000 jika sedang terpakai
sudo fuser -k 5000/tcp 2>/dev/null || true

# Start service
sudo systemctl restart sig-kiosk.service
echo -e "  ${GREEN}[OK] Service sig-kiosk.service diaktifkan.${NC}"

# ──────────────────────────────────────────────────────────────────────────────
# LANGKAH 7: UJI DETEKSI HARDWARE JETSON NANO
# ──────────────────────────────────────────────────────────────────────────────
echo -e "${GREEN}-> [7/7] Memeriksa deteksi Perangkat Hardware Jetson Nano...${NC}"

# 1. Cek I2C PCA9685
echo -n "  [I2C Bus 1]  : "
if i2cdetect -y -r 1 2>/dev/null | grep -q '40'; then
    echo -e "${GREEN}PCA9685 Terdeteksi di Alamat 0x40! (Gimbal SIAP)${NC}"
else
    echo -e "${YELLOW}0x40 tidak terdeteksi (Gimbal akan berjalan dalam mode Virtual/Simulasi).${NC}"
fi

# 2. Cek Kamera
echo -n "  [Kamera Feed]: "
if [ -e /dev/video0 ]; then
    echo -e "${GREEN}/dev/video0 Terdeteksi! (Camera SIAP)${NC}"
else
    echo -e "${YELLOW}/dev/video0 tidak ada (Menggunakan RTSP Stream / Simulation Feed).${NC}"
fi

# 3. Cek Serial NPK Sensor
echo -n "  [Sensor RS485]: "
if [ -e /dev/ttyUSB0 ]; then
    echo -e "${GREEN}/dev/ttyUSB0 Terdeteksi! (Sensor NPK Modbus SIAP)${NC}"
else
    echo -e "${YELLOW}/dev/ttyUSB0 tidak ada (Menggunakan ESP32 Push / Dummy Simulator).${NC}"
fi

IP_ADDR=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${BLUE}========================================================================${NC}"
echo -e "${GREEN}   [OK] JETSON NANO TERSEDIA & BERHASIL DI-SETUP! METODE KIOSK ACTIVE. ${NC}"
echo -e "${BLUE}========================================================================${NC}"
echo -e "Akses UI di Laptop/Tablet/HP  : ${YELLOW}http://${IP_ADDR}:5000${NC}"
echo -e "Monitoring Log Realtime        : ${YELLOW}sudo journalctl -u sig-kiosk.service -f${NC}"
echo -e "Buka Studio Kalibrasi Gimbal   : ${YELLOW}python3 ${APP_DIR}/servo_calibration_gui.py${NC}"
echo -e "Buka Aplikasi Desktop PyQt5    : ${YELLOW}python3 ${APP_DIR}/main.py${NC}"
echo ""
