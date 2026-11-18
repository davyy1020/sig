"""
Sistem Monitoring Kebun Berbasis AI Camera & Sensor NPK
========================================================
Entry point aplikasi desktop.

Menjalankan aplikasi PyQt5 dengan:
- Dark agriculture theme
- Form input data kebun
- Live camera monitoring
- Sensor NPK 7 in 1 (dummy)
- Database SQLite lokal
- Upload data via API

Usage:
    python main.py
"""

import sys
import os

# Tambahkan project root ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.main_window import MainWindow
from ui.styles import DARK_STYLE


def main():
    """Initialize and run the application."""
    # Enable High DPI support
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)

    # Apply global stylesheet
    app.setStyleSheet(DARK_STYLE)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Set application metadata
    app.setApplicationName("Sistem Monitoring Kebun")
    app.setOrganizationName("SIG Monitoring")
    app.setApplicationVersion("1.0.0")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
