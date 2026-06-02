"""
main.py — RaceVideo Studio entry point.
Run with:  python main.py
"""

import sys
import os

# ── Ensure project root is on sys.path ────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QIcon

from src.ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    qss_path = os.path.join(ROOT, "src", "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print(f"[WARN] stylesheet not found: {qss_path}")


def main() -> None:
    # Create output directory
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)

    # High-DPI support
    app = QApplication(sys.argv)
    app.setApplicationName("RaceVideo Studio")
    app.setApplicationDisplayName("RaceVideo Studio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RaceVideo")

    # Global font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    # Apply dark stylesheet
    load_stylesheet(app)

    # Launch main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
