#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from logging_config import setup_logging
from ui.main_window import MainWindow
from core.settings_manager import SettingsManager
from core.booru_source_manager import BooruSourceManager
from core.danbooru_client import DanbooruClient
from core.gelbooru_client import GelbooruClient
from core.rule34_client import Rule34Client
from core.yandere_client import YandereClient, KonachanClient
from ui.glassmorphism_style import GLASS_STYLE


def _set_dark_titlebar(hwnd):
    """Force Windows 10/11 dark title bar via DWM API."""
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    try:
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(ctypes.c_int(1)), ctypes.sizeof(ctypes.c_int)
        )
    except Exception:
        pass


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLASS_STYLE)

    settings = SettingsManager()

    # Create source manager and register all booru clients
    source_manager = BooruSourceManager(settings)
    source_manager.register_client(DanbooruClient(settings))
    source_manager.register_client(GelbooruClient(settings))
    source_manager.register_client(Rule34Client(settings))
    source_manager.register_client(YandereClient(settings))
    source_manager.register_client(KonachanClient(settings))
    source_manager.load_source_states()

    window = MainWindow(settings, source_manager)
    settings.restore_window_geometry(window)
    window.show()

    # Dark title bar
    _set_dark_titlebar(int(window.winId()))

    # Load startup workspace if configured
    startup = settings.startup_workspace
    if startup and window.workspace_manager.exists(startup):
        data = window.workspace_manager.load(startup)
        if data:
            window.current_workspace_name = startup
            window._restore_workspace_state(data)
            window.setWindowTitle(f"🧊 Booru Tag Editor Pro++ — {startup}")

    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
