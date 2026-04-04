"""
Universal Downloader — Application entry point.
Launches the PySide6 GUI application.
"""

import sys
import os

# Ensure the project root is on the path when running from any directory
_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.main_window import MainWindow
from ui.styles.theme import get_stylesheet


def main() -> None:
    # High-DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("UniversalDownloader")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("UniversalDownloader")

    # Apply dark theme
    app.setStyleSheet(get_stylesheet())

    # Default font
    font = QFont("Segoe UI", 10)
    font.setHintingPreference(QFont.PreferFullHinting)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
