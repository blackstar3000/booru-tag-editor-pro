GLASS_STYLE = """
QMainWindow, QWidget {
    background: #131415;
    color: #eee;
    font-family: "Segoe UI", "Helvetica Neue", sans-serif;
}
QMainWindow::separator {
    background: rgba(255,255,255,0.03);
    width: 2px;
}
QLabel {
    color: #ddd;
}
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8B5CF6, stop:1 #7C3AED);
    color: white;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #9B6CF6, stop:1 #8C4AED);
}
QPushButton:pressed {
    background: #6B2AED;
}
QLineEdit, QTextEdit {
    background: rgba(22,22,24,0.6);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 12px;
    color: #eee;
    font-size: 13px;
}
QLineEdit:focus, QTextEdit:focus {
    border: 1px solid #8B5CF6;
    background: rgba(22,22,24,0.8);
}
QListWidget {
    background: rgba(22,22,24,0.5);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    background: rgba(255,255,255,0.04);
    border-radius: 6px;
    padding: 6px 10px;
    margin: 2px 0;
    color: #eee;
}
QListWidget::item:selected {
    background: rgba(139,92,246,0.25);
    border: 1px solid #8B5CF6;
}
QScrollBar:vertical {
    background: rgba(22,22,24,0.3);
    width: 6px;
    border-radius: 3px;
}
QScrollBar::handle:vertical {
    background: #8B5CF6;
    border-radius: 3px;
    min-height: 30px;
}
QStatusBar {
    background: rgba(22,22,24,0.6);
    color: #999;
    border-top: 1px solid rgba(255,255,255,0.04);
}
"""