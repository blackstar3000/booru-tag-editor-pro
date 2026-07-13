from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QRadioButton, QButtonGroup, QDialogButtonBox, QMessageBox,
)
from PyQt5.QtCore import Qt

from ui.windows_theme import set_dark_title_bar, dark_question, dark_warning


class SaveWorkspaceDialog(QDialog):
    """Dialog for saving the current workspace state."""

    def __init__(self, parent, existing_names: list[str], current_name: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Save Workspace")
        self.setMinimumWidth(420)
        self.existing_names = [n.lower() for n in existing_names]
        self._result_name = ""
        self._result_mode = "new"  # "default" | "new" | "update"

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit(current_name)
        self.name_input.setPlaceholderText("Enter workspace name…")
        layout.addWidget(self.name_input)

        layout.addSpacing(8)

        self.radio_group = QButtonGroup(self)

        self.radio_new = QRadioButton("Save as New View")
        self.radio_new.setChecked(True)
        self.radio_group.addButton(self.radio_new, 0)
        layout.addWidget(self.radio_new)

        self.radio_update = QRadioButton("Update Existing View")
        self.radio_update.setEnabled(bool(existing_names))
        self.radio_group.addButton(self.radio_update, 1)
        layout.addWidget(self.radio_update)

        layout.addSpacing(8)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.name_input.returnPressed.connect(self._on_save)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            dark_warning(self, "Missing Name", "Please enter a workspace name.")
            return
        if name.lower() in self.existing_names and self.radio_new.isChecked():
            reply = dark_question(
                self, "Overwrite?",
                f"A workspace named '{name}' already exists.\nOverwrite it?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return
        self._result_name = name
        self._result_mode = "new" if self.radio_new.isChecked() else "update"
        self.accept()

    def result_name(self) -> str:
        return self._result_name

    def result_mode(self) -> str:
        return self._result_mode

    def showEvent(self, event):
        super().showEvent(event)
        set_dark_title_bar(self)
