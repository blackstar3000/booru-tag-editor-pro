from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QLabel,
    QLineEdit, QPushButton, QMenu, QAction, QMessageBox, QCompleter
)
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel
from core.tag_manager import TagManager
from core.danbooru_client import DanbooruClient
from ui.tag_inspector import TagInspector
import logging

logger = logging.getLogger(__name__)

class TagListWidget(QListWidget):
    orderChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)

    def dropEvent(self, event):
        super().dropEvent(event)
        new_order = [self.item(i).text() for i in range(self.count())]
        self.orderChanged.emit(new_order)


class TagPanel(QWidget):
    tags_changed = pyqtSignal(list)

    def __init__(self, tag_manager: TagManager, danbooru_client: DanbooruClient = None, parent=None):
        super().__init__(parent)
        self.tag_manager = tag_manager
        self.danbooru_client = danbooru_client
        self.all_tags = []
        self.filter_text = ""
        self.inspector = None
        self.setup_ui()
        self.tag_manager.tags_changed.connect(self._on_tags_changed)
        if self.danbooru_client:
            self.danbooru_client.autocomplete_results.connect(self._on_autocomplete_results)
            self.danbooru_client.tag_info_fetched.connect(self._on_tag_info_fetched)
            self.danbooru_client.tag_info_error.connect(self._on_tag_info_error)
            self.danbooru_client.credentials_missing.connect(self._on_credentials_missing)
            self.setup_autocomplete()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        self.label = QLabel("🏷️ Tags")
        layout.addWidget(self.label)

        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Filter tags...")
        self.search_input.textChanged.connect(self._filter_tags)
        row.addWidget(self.search_input)

        self.add_input = QLineEdit()
        self.add_input.setPlaceholderText("Add tag...")
        self.add_input.returnPressed.connect(self._add_tag)
        row.addWidget(self.add_input)

        self.add_btn = QPushButton("➕")
        self.add_btn.clicked.connect(self._add_tag)
        row.addWidget(self.add_btn)

        layout.addLayout(row)

        self.tag_list = TagListWidget()
        self.tag_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.tag_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tag_list.customContextMenuRequested.connect(self._show_context_menu)
        self.tag_list.itemDoubleClicked.connect(self._on_item_double_click)
        self.tag_list.orderChanged.connect(self._on_order_changed)
        layout.addWidget(self.tag_list)

    def setup_autocomplete(self):
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.add_input.setCompleter(self.completer)
        self.add_input.textChanged.connect(self._on_text_changed_for_autocomplete)

    def _on_text_changed_for_autocomplete(self, text):
        if len(text) >= 2 and self.danbooru_client:
            self.danbooru_client.autocomplete(text)

    def _on_autocomplete_results(self, query, tags):
        if self.add_input.text().startswith(query):
            self.model.setStringList(tags)
            self.completer.complete()

    def _on_item_double_click(self, item):
        tag = item.text()
        if self.danbooru_client:
            self.show_tag_inspector(tag)

    def show_tag_inspector(self, tag):
        """Show the tag inspector as a separate popup window."""
        if not self.inspector:
            # Create without a parent to ensure it's a separate window
            self.inspector = TagInspector()
        self.inspector.clear()
        self.inspector.show()
        self.inspector.raise_()
        if self.danbooru_client:
            self.danbooru_client.fetch_tag_info(tag)

    def _on_tag_info_fetched(self, tag, info):
        if self.inspector and self.inspector.isVisible():
            self.inspector.display_tag_info(tag, info)

    def _on_tag_info_error(self, tag, error):
        if self.inspector and self.inspector.isVisible():
            self.inspector.display_tag_info(tag, {"error": error})

    def _on_credentials_missing(self):
        reply = QMessageBox.question(
            self, "Credentials Needed",
            "Danbooru API credentials are not set.\n"
            "Would you like to open settings now?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'open_settings'):
                    parent.open_settings()
                    break
                parent = parent.parent()

    def _on_tags_changed(self, new_tags):
        self.all_tags = new_tags
        self._apply_filter()

    def _apply_filter(self):
        filter_text = self.search_input.text().strip().lower()
        self.tag_list.clear()
        filtered = [t for t in self.all_tags if filter_text in t.lower()]
        for tag in filtered:
            self.tag_list.addItem(tag)
        self.tags_changed.emit(filtered)
        self.tag_list.setDragEnabled(not bool(filter_text))

    def _filter_tags(self, text):
        self.filter_text = text.strip().lower()
        self._apply_filter()

    def _add_tag(self):
        text = self.add_input.text().strip()
        if text:
            self.tag_manager.add_tag(text)
            self.add_input.clear()

    def _show_context_menu(self, pos):
        menu = QMenu()
        inspect_action = QAction("🔍 Inspect Tag", self)
        inspect_action.triggered.connect(self._inspect_selected)
        menu.addAction(inspect_action)
        delete_action = QAction("🗑️ Delete Selected", self)
        delete_action.triggered.connect(self._delete_selected)
        menu.addAction(delete_action)
        delete_all_action = QAction("Delete All Tags", self)
        delete_all_action.triggered.connect(self._delete_all)
        menu.addAction(delete_all_action)
        menu.exec_(self.tag_list.mapToGlobal(pos))

    def _inspect_selected(self):
        items = self.tag_list.selectedItems()
        if items and self.danbooru_client:
            tag = items[0].text()
            self.show_tag_inspector(tag)

    def _delete_selected(self):
        items = self.tag_list.selectedItems()
        if items:
            tags_to_delete = [item.text() for item in items]
            self.tag_manager.remove_tags(tags_to_delete)

    def _delete_all(self):
        if self.all_tags:
            reply = QMessageBox.question(
                self, "Delete All",
                f"Delete all {len(self.all_tags)} tags?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.tag_manager.set_tags([])

    def _on_order_changed(self, new_order):
        self.tag_manager.reorder_tags(new_order)

    def get_selected_tags(self):
        return [item.text() for item in self.tag_list.selectedItems()]

    def clear(self):
        self.tag_list.clear()
        self.all_tags = []
        self.search_input.clear()
        self.add_input.clear()
        if self.inspector:
            self.inspector.close()
            self.inspector = None