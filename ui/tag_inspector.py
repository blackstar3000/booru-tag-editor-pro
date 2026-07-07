from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QScrollArea, QPushButton
from PyQt5.QtCore import Qt

class TagInspector(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window)
        self.setWindowTitle("Smart Tag Inspector")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)
        self.clear()

    def display_tag_info(self, tag: str, info: dict):
        self.clear()
        if not info:
            self.content_layout.addWidget(QLabel(f"Tag: {tag}\nNo info available."))
            settings_btn = QPushButton("Open Settings to set Danbooru credentials")
            settings_btn.clicked.connect(self._open_settings)
            self.content_layout.addWidget(settings_btn)
            return
        if "error" in info:
            self.content_layout.addWidget(QLabel(f"Tag: {tag}\nError: {info['error']}"))
            settings_btn = QPushButton("Open Settings to check credentials")
            settings_btn.clicked.connect(self._open_settings)
            self.content_layout.addWidget(settings_btn)
            return
        name = info.get('name', tag)
        category = info.get('category', 'unknown')
        post_count = info.get('post_count', 0)
        description = info.get('description', '')
        aliases = info.get('aliases', [])
        implications = info.get('implications', [])
        parents = info.get('parents', [])

        self.content_layout.addWidget(QLabel(f"<b>{name}</b>"))
        self.content_layout.addWidget(QLabel(f"Category: {category}"))
        self.content_layout.addWidget(QLabel(f"Post count: {post_count}"))
        if description:
            desc_label = QLabel("Description:")
            desc_label.setStyleSheet("font-weight: bold;")
            self.content_layout.addWidget(desc_label)
            desc_text = QTextEdit()
            desc_text.setReadOnly(True)
            desc_text.setPlainText(description)
            desc_text.setMaximumHeight(100)
            self.content_layout.addWidget(desc_text)
        if aliases:
            self.content_layout.addWidget(QLabel(f"Aliases: {', '.join(aliases)}"))
        if implications:
            self.content_layout.addWidget(QLabel(f"Implications: {', '.join(implications)}"))
        if parents:
            self.content_layout.addWidget(QLabel(f"Parents: {', '.join(parents)}"))
        self.content_layout.addStretch()

    def _open_settings(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, 'open_settings'):
                parent.open_settings()
                break
            parent = parent.parent()

    def clear(self):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)