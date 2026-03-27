from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("BAC Автопарк")
    app.setOrganizationName("BAC")
    window = MainWindow()
    window.show()
    return app.exec()
