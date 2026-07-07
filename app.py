#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from logging_config import setup_logging
from ui.main_window import MainWindow
from core.settings_manager import SettingsManager
from core.danbooru_client import DanbooruClient
from ui.glassmorphism_style import GLASS_STYLE

def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLASS_STYLE)

    settings = SettingsManager()
    danbooru_client = DanbooruClient(settings)
    window = MainWindow(settings, danbooru_client)
    settings.restore_window_geometry(window)
    window.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())