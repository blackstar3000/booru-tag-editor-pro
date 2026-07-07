from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel

class MetadataPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.label = QLabel("📋 Metadata")
        layout.addWidget(self.label)
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Load an image to see metadata.")
        layout.addWidget(self.text_edit)

    def set_metadata(self, metadata):
        if metadata:
            text = "\n".join([f"{k}: {v}" for k, v in metadata.items()])
            self.text_edit.setText(text)
        else:
            self.text_edit.setText("No metadata found.")

    def clear(self):
        self.text_edit.clear()