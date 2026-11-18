#!/bin/bash
# ==============================================================================
# Script untuk Mematikan & Nonaktifkan Auto-Run SIG Server pada Orange Pi
# ==============================================================================
echo "=========================================================="
echo "   MEMATIKAN & MEMNONAKTIFKAN AUTORUN (sig-kiosk.service) "
echo "=========================================================="

echo orangepi | sudo -S systemctl stop sig-kiosk.service
echo orangepi | sudo -S systemctl disable sig-kiosk.service
echo orangepi | sudo -S fuser -k 5000/tcp 2>/dev/null

echo ""
echo "[OK] Auto-run systemd service 'sig-kiosk.service' telah DIMATIKAN dan DINONAKTIFKAN secara permanen."
