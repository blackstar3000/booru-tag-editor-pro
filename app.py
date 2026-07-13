#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
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
from ui.windows_theme import set_dark_title_bar


def main():
    setup_logging()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(GLASS_STYLE)

    # Dark palette for Fusion popups (combo dropdowns, menus) that don't use stylesheet
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(18, 20, 28))
    palette.setColor(QPalette.WindowText, QColor(204, 204, 204))
    palette.setColor(QPalette.Base, QColor(18, 20, 28))
    palette.setColor(QPalette.AlternateBase, QColor(22, 24, 32))
    palette.setColor(QPalette.ToolTipBase, QColor(18, 20, 28))
    palette.setColor(QPalette.ToolTipText, QColor(204, 204, 204))
    palette.setColor(QPalette.Text, QColor(204, 204, 204))
    palette.setColor(QPalette.Button, QColor(18, 20, 28))
    palette.setColor(QPalette.ButtonText, QColor(204, 204, 204))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(139, 92, 246))
    palette.setColor(QPalette.Highlight, QColor(139, 92, 246, 64))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
    app.setPalette(palette)

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
    set_dark_title_bar(window)

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
