#!/bin/bash
# ==============================================================================
# Script untuk Mengaktifkan & Menjalankan Auto-Run SIG Server pada Orange Pi
# ==============================================================================
echo "=========================================================="
echo "   MENGAKTIFKAN SYSTEMD AUTORUN (sig-kiosk.service)      "
echo "=========================================================="

echo orangepi | sudo -S chmod 666 /dev/i2c* /dev/video* 2>/dev/null
echo orangepi | sudo -S cp /home/orangepi/sig/sig-kiosk.service /etc/systemd/system/sig-kiosk.service
echo orangepi | sudo -S systemctl daemon-reload
echo orangepi | sudo -S systemctl enable sig-kiosk.service
echo orangepi | sudo -S fuser -k 5000/tcp 2>/dev/null
echo orangepi | sudo -S systemctl restart sig-kiosk.service

echo ""
echo "[OK] Auto-run systemd service 'sig-kiosk.service' telah DIAKTIFKAN dan DIJALANKAN!"
echo "Status Service saat ini:"
echo orangepi | sudo -S systemctl status sig-kiosk.service --no-pager
