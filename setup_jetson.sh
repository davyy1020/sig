#!/bin/bash
# ==============================================================================
# SCRIPT SETUP AUTOMATION UNTUK SIG UI / GIMBAL / SENSOR DI NVIDIA JETSON NANO
# Jalankan di Jetson Nano: sudo bash setup_jetson.sh
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ACTUAL_USER="${SUDO_USER:-$USER}"
if [ "$ACTUAL_USER" = "root" ]; then
    ACTUAL_USER="sigma"
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_DIR="$SCRIPT_DIR"

echo -e "${BLUE}==========================================================${NC}"
echo -e "${BLUE}   SETUP & AUTORUN INSTALLER FOR SIG UI (JETSON NANO)    ${NC}"
echo -e "${BLUE}==========================================================${NC}"
echo -e "User Target     : ${YELLOW}${ACTUAL_USER}${NC}"
echo -e "Directory App   : ${YELLOW}${APP_DIR}${NC}"
echo ""

# 1. Update paket & Install Dependensi Sistem Jetson Nano (Ubuntu 18.04 / 20.04)
echo -e "${GREEN}-> [1/5] Memeriksa & menginstall dependensi sistem Linux...${NC}"
sudo apt update -y || true
sudo apt install -y python3 python3-pip python3-dev i2c-tools libgl1-mesa-glx libglib2.0-0 rsync unzip openssl || true

# 2. Pengaturan Izin Akses Hardware Jetson Nano (I2C Bus 1, Video Camera, Serial UART)
echo -e "${GREEN}-> [2/5] Mengatur izin akses hardware (I2C, Video, Serial)...${NC}"
sudo chmod 666 /dev/i2c* 2>/dev/null || true
sudo chmod 666 /dev/video* 2>/dev/null || true
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || true
sudo chmod 666 /dev/ttyTHS* 2>/dev/null || true

# Matikan nvgetty agar port UART /dev/ttyTHS1 bebas dipakai komunikasi RX/TX ke ESP32
sudo systemctl stop nvgetty 2>/dev/null || true
sudo systemctl disable nvgetty 2>/dev/null || true

# Tambahkan user ke grup i2c, video, dialout
sudo usermod -aG i2c,video,dialout "$ACTUAL_USER" 2>/dev/null || true
sudo usermod -aG i2c,video,dialout sigma 2>/dev/null || true

# 3. Install Python Dependencies (Sesuai Python 3.6 di Jetson Nano)
echo -e "${GREEN}-> [3/5] Menginstall dependensi Python (Python 3.6)...${NC}"
if [ -f "$APP_DIR/requirements.txt" ]; then
    pip3 install -r "$APP_DIR/requirements.txt" --break-system-packages 2>/dev/null || pip3 install -r "$APP_DIR/requirements.txt"
fi
pip3 install flask requests opencv-python-headless numpy pillow pyserial smbus2 --break-system-packages 2>/dev/null || pip3 install flask requests opencv-python-headless numpy pillow pyserial smbus2

# Buat self-signed SSL cert jika belum ada (agar GPS browser bekerja via HTTPS)
SSL_DIR="${APP_DIR}/ui/ssl"
mkdir -p "$SSL_DIR"
if [ ! -f "${SSL_DIR}/cert.pem" ] || [ ! -f "${SSL_DIR}/key.pem" ]; then
    echo -e "${GREEN}[SSL] Membuat self-signed certificate untuk HTTPS...${NC}"
    openssl req -x509 -newkey rsa:2048 -keyout "${SSL_DIR}/key.pem" -out "${SSL_DIR}/cert.pem" \
        -days 3650 -nodes -subj "/CN=SIG-Kiosk/O=SIG/C=ID" 2>/dev/null || true
    echo -e "${GREEN}[SSL] Certificate selesai dibuat di ${SSL_DIR}${NC}"
fi

# 4. Konfigurasi Systemd Service (Autorun Kiosk Server)
echo -e "${GREEN}-> [4/5] Mengatur Auto-run Systemd Service (sig-kiosk.service)...${NC}"

SERVICE_FILE="/etc/systemd/system/sig-kiosk.service"

cat <<EOF | sudo tee $SERVICE_FILE > /dev/null
[Unit]
Description=SIG Kiosk Web Server & Jetson Nano Gimbal Controller
After=network.target multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}/ui
ExecStartPre=/bin/bash -c "chmod 666 /dev/i2c* /dev/video* /dev/ttyUSB* /dev/ttyTHS* || true"
ExecStart=/usr/bin/python3 ${APP_DIR}/ui/app.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload & Enable service
sudo systemctl daemon-reload
sudo systemctl enable sig-kiosk.service

# Stop port 5000 jika sedang dipakai oleh proses manual
sudo fuser -k 5000/tcp 2>/dev/null || true

# Restart service
echo -e "${GREEN}-> [5/5] Menjalankan service SIG UI di Jetson Nano...${NC}"
sudo systemctl restart sig-kiosk.service

echo ""
echo -e "${BLUE}==========================================================${NC}"
echo -e "${GREEN} [OK] PROSES SETUP & DEPLOYMENT JETSON NANO SELESAI!${NC}"
echo -e "${BLUE}==========================================================${NC}"
echo -e "Status Service saat ini:"
sudo systemctl status sig-kiosk.service --no-pager
echo ""
echo -e "Akses UI di Browser Laptop/HP : ${YELLOW}http://$(hostname -I | awk '{print $1}'):5000${NC}"
echo -e "Cek Log Realtime Systemd     : ${YELLOW}sudo journalctl -u sig-kiosk.service -f${NC}"
echo ""
