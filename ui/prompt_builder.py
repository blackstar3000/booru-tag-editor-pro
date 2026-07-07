# ui/prompt_builder.py
"""
Prompt Builder – build a prompt by selecting tags from categorized sections.
"""

import json
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QScrollArea,
    QPushButton, QLabel, QTextEdit, QFrame, QGridLayout, QMessageBox,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox, QCheckBox,
    QSplitter, QCompleter
)
from PyQt5.QtCore import Qt, pyqtSignal, QStringListModel
from PyQt5.QtGui import QClipboard, QGuiApplication
import logging

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    "Quality", "Character", "Copyright", "Artist", "Style",
    "Appearance", "Expression", "Clothing", "Accessories",
    "Pose", "Camera", "Lighting", "Environment", "Effects",
    "Meta", "Uncategorized"
]

DEFAULT_ORDER = [
    "Quality", "Character", "Copyright", "Artist", "Style",
    "Appearance", "Expression", "Clothing", "Accessories",
    "Pose", "Camera", "Lighting", "Environment", "Effects",
    "Meta", "Uncategorized"
]

class PromptBuilder(QWidget):
    prompt_changed = pyqtSignal(str)
    seed_requested = pyqtSignal()

    def __init__(self, danbooru_client=None, parent=None):
        super().__init__(parent)
        self.danbooru_client = danbooru_client
        self.categories = {}
        self.category_order = DEFAULT_ORDER.copy()
        self.setup_ui()
        self.load_categories()
        if self.danbooru_client:
            self.setup_autocomplete()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(4, 4, 4, 4)

        top_row = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.category_order)
        top_row.addWidget(self.category_combo)

        self.add_tag_input = QLineEdit()
        self.add_tag_input.setPlaceholderText("Add tag...")
        self.add_tag_input.returnPressed.connect(self._add_tag_to_category)
        top_row.addWidget(self.add_tag_input)

        self.add_tag_btn = QPushButton("Add")
        self.add_tag_btn.clicked.connect(self._add_tag_to_category)
        top_row.addWidget(self.add_tag_btn)

        left_layout.addLayout(top_row)

        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.tag_list.itemDoubleClicked.connect(self._remove_selected_tags)
        left_layout.addWidget(self.tag_list)

        btn_row = QHBoxLayout()
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._remove_selected_tags)
        btn_row.addWidget(self.remove_btn)

        self.clear_cat_btn = QPushButton("Clear Category")
        self.clear_cat_btn.clicked.connect(self._clear_category)
        btn_row.addWidget(self.clear_cat_btn)

        btn_row.addStretch()
        left_layout.addLayout(btn_row)

        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(4, 4, 4, 4)

        fmt_row = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Comma Separated", "Multi-Line", "Grouped by Category", "Compact"])
        self.format_combo.currentIndexChanged.connect(self.update_preview)
        fmt_row.addWidget(QLabel("Format:"))
        fmt_row.addWidget(self.format_combo)

        self.include_negative = QCheckBox("Include Negative Prompt")
        self.include_negative.setChecked(False)
        self.include_negative.toggled.connect(self.update_preview)
        fmt_row.addWidget(self.include_negative)

        fmt_row.addStretch()
        right_layout.addLayout(fmt_row)

        self.preview_label = QLabel("Prompt Preview:")
        right_layout.addWidget(self.preview_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText("Select categories and tags to build your prompt...")
        right_layout.addWidget(self.preview_text)

        self.stats_label = QLabel("Tags: 0 | Categories: 0 | Tokens: 0")
        right_layout.addWidget(self.stats_label)

        action_row = QHBoxLayout()
        self.copy_btn = QPushButton("📋 Copy Prompt")
        self.copy_btn.clicked.connect(self.copy_prompt)
        action_row.addWidget(self.copy_btn)

        self.apply_btn = QPushButton("🏷️ Apply to Tags")
        self.apply_btn.clicked.connect(self.apply_to_tags)
        action_row.addWidget(self.apply_btn)

        self.clear_all_btn = QPushButton("🗑️ Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all)
        action_row.addWidget(self.clear_all_btn)

        self.seed_btn = QPushButton("🌱 Send from Image Tags")
        self.seed_btn.clicked.connect(self.seed_requested.emit)
        action_row.addWidget(self.seed_btn)

        action_row.addStretch()
        right_layout.addLayout(action_row)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._on_category_changed()

    def setup_autocomplete(self):
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel()
        self.completer.setModel(self.model)
        self.add_tag_input.setCompleter(self.completer)
        self.add_tag_input.textChanged.connect(self._on_text_changed_for_autocomplete)

    def _on_text_changed_for_autocomplete(self, text):
        if len(text) >= 2 and self.danbooru_client:
            self.danbooru_client.autocomplete(text)
            # Connect the client's autocomplete signal to update the completer
            # We'll connect once and reuse (but must avoid multiple connections)
            try:
                self.danbooru_client.autocomplete_results.disconnect(self._on_autocomplete_results)
            except:
                pass
            self.danbooru_client.autocomplete_results.connect(self._on_autocomplete_results)

    def _on_autocomplete_results(self, query, tags):
        if self.add_tag_input.text().startswith(query):
            self.model.setStringList(tags)
            self.completer.complete()

    def _on_category_changed(self):
        current_cat = self.category_combo.currentText()
        self.tag_list.clear()
        if current_cat in self.categories:
            for tag in self.categories[current_cat]:
                item = QListWidgetItem(tag)
                self.tag_list.addItem(item)

    def _add_tag_to_category(self):
        tag = self.add_tag_input.text().strip()
        if not tag:
            return
        current_cat = self.category_combo.currentText()
        if current_cat not in self.categories:
            self.categories[current_cat] = []
        if tag not in self.categories[current_cat]:
            self.categories[current_cat].append(tag)
            self.add_tag_input.clear()
            self._on_category_changed()
            self.update_preview()

    def _remove_selected_tags(self):
        current_cat = self.category_combo.currentText()
        selected = self.tag_list.selectedItems()
        if selected:
            to_remove = [item.text() for item in selected]
            if current_cat in self.categories:
                self.categories[current_cat] = [t for t in self.categories[current_cat] if t not in to_remove]
                self._on_category_changed()
                self.update_preview()

    def _clear_category(self):
        current_cat = self.category_combo.currentText()
        if current_cat in self.categories and self.categories[current_cat]:
            if QMessageBox.question(self, "Clear Category", f"Clear all tags in '{current_cat}'?") == QMessageBox.Yes:
                self.categories[current_cat].clear()
                self._on_category_changed()
                self.update_preview()

    def clear_all(self):
        if QMessageBox.question(self, "Clear All", "Clear all tags from all categories?") == QMessageBox.Yes:
            for cat in self.categories:
                self.categories[cat].clear()
            self._on_category_changed()
            self.update_preview()

    def load_categories(self):
        json_path = Path(__file__).parent.parent / "prompt_categories.json"
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.categories = data.get('categories', {})
                self.category_order = data.get('order', DEFAULT_ORDER)
                logger.info(f"Loaded prompt categories from {json_path}")
            except Exception as e:
                logger.warning(f"Failed to load prompt categories: {e}")
                self._create_defaults()
        else:
            self._create_defaults()
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({'categories': self.categories, 'order': self.category_order}, f, indent=2)
                logger.info(f"Saved default prompt categories to {json_path}")
            except:
                pass

        self.category_combo.clear()
        self.category_combo.addItems(self.category_order)
        self._on_category_changed()

    def _create_defaults(self):
        self.categories = {cat: [] for cat in DEFAULT_CATEGORIES}
        self.category_order = DEFAULT_ORDER.copy()

    def seed_from_tags(self, tags):
        for cat in self.categories:
            self.categories[cat].clear()
        if 'Uncategorized' not in self.categories:
            self.categories['Uncategorized'] = []
        self.categories['Uncategorized'] = tags.copy()
        imported = len(tags)
        self._on_category_changed()
        self.update_preview()
        return imported

    def update_preview(self):
        format_mode = self.format_combo.currentText()
        include_negative = self.include_negative.isChecked()

        ordered = []
        for cat in self.category_order:
            if cat in self.categories and self.categories[cat]:
                ordered.append((cat, self.categories[cat]))

        if format_mode == "Comma Separated":
            all_tags = []
            for cat, tags in ordered:
                all_tags.extend(tags)
            prompt = ", ".join(all_tags)
        elif format_mode == "Multi-Line":
            lines = []
            for cat, tags in ordered:
                lines.extend(tags)
            prompt = "\n".join(lines)
        elif format_mode == "Grouped by Category":
            sections = []
            for cat, tags in ordered:
                sections.append(f"### {cat}")
                sections.extend(tags)
                sections.append("")
            prompt = "\n".join(sections)
        else:  # Compact
            all_tags = []
            for cat, tags in ordered:
                all_tags.extend(tags)
            prompt = ", ".join(all_tags)

        self.preview_text.setText(prompt)
        self.prompt_changed.emit(prompt)

        total_tags = sum(len(tags) for tags in self.categories.values())
        token_estimate = len(prompt) // 4
        self.stats_label.setText(f"Tags: {total_tags} | Categories: {len(self.categories)} | Tokens: {token_estimate}")

    def copy_prompt(self):
        prompt = self.preview_text.toPlainText()
        if prompt:
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(prompt)
            logger.info("Prompt copied to clipboard")

    def apply_to_tags(self):
        prompt = self.preview_text.toPlainText()
        if prompt:
            self.prompt_changed.emit(prompt)