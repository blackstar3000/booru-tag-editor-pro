# ui/prompt_builder.py
"""
Prompt Builder – build a prompt by selecting tags from categorized sections.
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QMessageBox,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox, QCheckBox,
    QSplitter, QMenu, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QClipboard, QGuiApplication
from core.danbooru_tag_db import DanbooruTagDB
from core.advanced_bulk import AdvancedBulkOperations
from ui.tag_autocomplete import TagAutocompletePopup, TagEntry
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

GENERAL_KEYWORD_MAP = {
    "Quality": [
        "masterpiece", "best quality", "highres", "ultra detailed",
        "high quality", "highly detailed", "detailed", "perfect",
        "beautiful", "gorgeous", "stunning", "magnificent",
        "hq", "hd", "8k", "4k", "sharp focus", "professional",
    ],
    "Style": [
        "watercolor", "sketch", "lineart", "anime style", "realistic",
        "semi-realistic", "chibi", "pixel art", "3d render", "cgi",
        "oil painting", "digital painting", "illustration", "artwork",
        "cell shade", "cel shade", "flat color", "monochrome",
        "grayscale", "ink", "marker", "pastel", "vibrant",
    ],
    "Expression": [
        "smile", "blush", "frown", "angry", "happy", "sad", "crying",
        "laugh", "laughing", "grin", "serious", "surprised", "shock",
        "scared", "fear", "embarrassed", "shy", "confident", "wink",
        "tongue out", "pout", "teeth", "face", "facial expression",
        "expression", "look", "stare", "gaze", "eye contact",
    ],
    "Appearance": [
        "long hair", "short hair", "blonde hair", "brown hair",
        "black hair", "white hair", "silver hair", "blue hair",
        "pink hair", "purple hair", "green hair", "red hair",
        "orange hair", "multicolored hair", "hair ornament",
        "ponytail", "twintails", "braid", "bun", "bangs",
        "ahoge", "sidehair", "drill hair", "curly hair",
        "straight hair", "wavy hair", "hairpin", "hair flower",
        "blue eyes", "green eyes", "red eyes", "brown eyes",
        "grey eyes", "purple eyes", "yellow eyes", "golden eyes",
        "heterochromia", "glasses", "sunglasses", "monocle",
        "freckles", "beard", "mustache", "tan", "pale skin",
        "dark skin", "fair skin", "eyebrow", "eyelash",
    ],
    "Clothing": [
        "dress", "skirt", "shirt", "blouse", "pants", "jeans",
        "shorts", "jacket", "coat", "hoodie", "sweater", "vest",
        "hat", "cap", "beret", "crown", "tiara", "headband",
        "ribbon", "bow", "necktie", "scarf", "gloves", "mittens",
        "socks", "stockings", "pantyhose", "thighhighs", "tights",
        "shoes", "boots", "sandal", "loafers", "heels",
        "uniform", "suit", "armor", "robe", "kimono", "yukata",
        "swimsuit", "bikini", "one-piece", "underwear", "lingerie",
        "bra", "panties", "apron", "cloak", "cape", "belt",
        "necklace", "choker", "bracelet", "ring", "earrings",
        "outfit", "clothing", "wear", "gown", "mini skirt",
        "pleated skirt", "sailor uniform", "school uniform",
    ],
    "Accessories": [
        "sword", "katana", "blade", "wand", "staff", "shield",
        "gun", "pistol", "rifle", "bow", "arrow", "knife", "dagger",
        "spear", "lance", "axe", "hammer", "scythe", "whip",
        "book", "grimoire", "scroll", "umbrella", "parasol",
        "mask", "headphones", "headset", "goggles", "camera",
        "phone", "smartphone", "cup", "teacup", "glass", "bottle",
        "food", "fruit", "flower", "bouquet", "bag", "backpack",
        "purse", "jewelry", "instrument", "guitar", "microphone",
        "glasses", "crown", "ribbon", "bell", "wing", "tail",
        "halo", "demon horn", "animal ear", "cat ear",
    ],
    "Pose": [
        "sitting", "standing", "lying", "laying", "laying down",
        "kneeling", "crouching", "squatting", "bending", "leaning",
        "stretching", "jumping", "running", "walking", "dancing",
        "sleeping", "resting", "pointing", "holding", "reaching",
        "crossed arms", "folded hands", "hand up", "hand on hip",
        "arms up", "arms behind", "leg up", "spread legs",
        "pose", "posture", "gesture", "hand gesture", "peace sign",
        "victory sign", "thumbs up", "salute", "bow", "curtsey",
    ],
    "Camera": [
        "close-up", "closeup", "close_up", "dutch angle",
        "aerial view", "bird's eye", "worm's eye", "low angle",
        "high angle", "rear view", "side view", "profile",
        "from behind", "from side", "from above", "from below",
        "straight on", "cowboy shot", "medium shot", "wide shot",
        "full body", "upper body", "lower body", "face focus",
        "portrait", "headshot", "pov", "first person",
        "overhead", "over-the-shoulder",
    ],
    "Lighting": [
        "backlight", "back light", "rim light", "glow", "glowing",
        "neon", "neon light", "dark", "bright", "sunlight",
        "moonlight", "candlelight", "lamp", "flash", "strobe",
        "volumetric", "god rays", "crepuscular", "soft light",
        "hard light", "diffuse", "ambient", "studio light",
        "cinematic", "dramatic", "moody", "shadow", "shade",
        "silhouette", "highlight", "reflection",
    ],
    "Environment": [
        "sky", "cloud", "sunset", "sunrise", "night", "day",
        "sea", "ocean", "lake", "river", "water", "beach",
        "shore", "coast", "forest", "woods", "tree", "mountain",
        "hill", "field", "grass", "flower", "garden", "park",
        "city", "town", "village", "street", "road", "path",
        "building", "house", "castle", "ruin", "temple", "church",
        "room", "bedroom", "kitchen", "bathroom", "classroom",
        "office", "library", "stage", "balcony", "rooftop",
        "desert", "snow", "ice", "winter", "summer", "spring",
        "autumn", "fall", "rain", "storm", "lightning", "thunder",
        "wind", "fog", "mist", "smoke", "fire", "flame",
        "space", "star", "moon", "planet", "underwater",
        "indoor", "outdoor", "nature", "urban", "countryside",
        "bridge", "fountain", "bench", "stair", "door", "window",
    ],
    "Effects": [
        "blur", "motion blur", "depth of field", "bokeh",
        "particle", "sparkle", "spark", "explosion", "burst",
        "smoke", "fog effect", "mist effect", "steam", "bubble",
        "glitter", "aura", "halo effect", "lens flare",
        "sunflare", "light rays", "light shaft", "shadow",
        "grain", "film grain", "noise", "vignette",
        "chromatic aberration", "splash", "blood", "sweat",
        "tear", "teardrop", "petal", "leaf", "sakura",
        "confetti", "rainbow", "starburst", "glint",
    ],
}


class PromptBuilder(QWidget):
    prompt_changed = pyqtSignal(str)
    seed_requested = pyqtSignal()
    grouping_completed = pyqtSignal(str)

    def __init__(self, danbooru_client=None, tag_db: DanbooruTagDB = None, parent=None):
        super().__init__(parent)
        self.danbooru_client = danbooru_client
        self.tag_db = tag_db
        self.categories = {}
        self.category_order = DEFAULT_ORDER.copy()
        self.tag_order = []
        self._all_data = {'images': {}, 'order': DEFAULT_ORDER.copy()}
        self.current_image_key = None
        self._autocomplete_connected = False
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

        fr_row = QHBoxLayout()
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        fr_row.addWidget(self.find_input)

        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")
        fr_row.addWidget(self.replace_input)

        self.regex_check = QCheckBox("Regex")
        self.regex_check.setToolTip("Treat 'Find' as a regular expression instead of plain text.")
        fr_row.addWidget(self.regex_check)

        self.find_replace_btn = QPushButton("Replace All")
        self.find_replace_btn.setToolTip(
            "Renames the tag everywhere it appears (its category and its\n"
            "position in the prompt are both preserved)."
        )
        self.find_replace_btn.clicked.connect(self._apply_find_replace)
        fr_row.addWidget(self.find_replace_btn)

        left_layout.addLayout(fr_row)

        self.tag_list = QListWidget()
        self.tag_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.tag_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tag_list.customContextMenuRequested.connect(self._show_tag_context_menu)
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

        self.reorder_btn = QPushButton("🔀 Reorder Words")
        self.reorder_btn.setToolTip("Drag tags into a new order for the prompt, independent of category.")
        self.reorder_btn.clicked.connect(self._open_reorder_dialog)
        action_row.addWidget(self.reorder_btn)

        # “Send from Image Tags” with a mode toggle
        row = QHBoxLayout()
        self.seed_btn = QPushButton("🌱 Send from Image Tags")
        self.seed_btn.clicked.connect(self._on_seed_requested)
        row.addWidget(self.seed_btn)

        self.replace_check = QCheckBox("Replace (clear first)")
        self.replace_check.setChecked(False)  # <-- now unchecked by default (merge)
        self.replace_check.setToolTip(
            "When checked: clears all existing tags before importing.\n"
            "When unchecked (default): merges new tags with existing categories (preserves manual edits)."
        )
        row.addWidget(self.replace_check)
        row.addStretch()
        action_row.addLayout(row)

        action_row.addStretch()
        right_layout.addLayout(action_row)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._on_category_changed()

    def _on_seed_requested(self):
        self.seed_requested.emit()

    def setup_autocomplete(self):
        self._autocomplete_popup = TagAutocompletePopup(self)
        self._autocomplete_popup.install_on(self.add_tag_input)
        self._autocomplete_popup.tag_selected.connect(self._on_tag_selected)
        self.add_tag_input.textChanged.connect(self._on_text_changed_for_autocomplete)

    def _on_tag_selected(self, tag):
        self.add_tag_input.setText(tag)
        self._add_tag_to_category()

    def _on_text_changed_for_autocomplete(self, text):
        if len(text) < 1:
            self._autocomplete_popup.hide()
            return
        results = self.tag_db.search(text) if self.tag_db and self.tag_db.is_loaded else []
        anchor = self.add_tag_input.geometry()
        global_point = self.add_tag_input.parentWidget().mapToGlobal(
            anchor.bottomLeft()) if self.add_tag_input.parentWidget() else \
            self.add_tag_input.mapToGlobal(anchor.bottomLeft())
        api_rect = QRect(global_point, anchor.size())
        api_rect.setHeight(0)
        if results:
            self._autocomplete_popup.show_suggestions(
                [TagEntry(r['name'], r['category'], r['post_count'], source='db') for r in results],
                api_rect
            )
        else:
            self._autocomplete_popup.hide()
        if self.danbooru_client:
            if not self._autocomplete_connected:
                self.danbooru_client.autocomplete_results.connect(self._on_autocomplete_results)
                self.danbooru_client.autocomplete_error.connect(lambda q, e: logger.warning(f"Autocomplete error for '{q}': {e}"))
                self._autocomplete_connected = True
            self.danbooru_client.autocomplete(text)

    def _on_autocomplete_results(self, query, tags):
        if not self.add_tag_input.text().startswith(query):
            return
        if not tags:
            return
        db_results = self.tag_db.search(self.add_tag_input.text()) if self.tag_db and self.tag_db.is_loaded else []
        seen = {r['name'] for r in db_results}
        merged = [TagEntry(r['name'], r['category'], r['post_count'], source='db') for r in db_results]
        for t in tags:
            name = t['name'] if isinstance(t, dict) else t
            if name not in seen:
                if isinstance(t, dict):
                    merged.append(TagEntry(t['name'], t.get('category', 0), t.get('post_count', 0)))
                else:
                    merged.append(TagEntry(t))
                seen.add(name)
        anchor = self.add_tag_input.geometry()
        global_point = self.add_tag_input.parentWidget().mapToGlobal(
            anchor.bottomLeft()) if self.add_tag_input.parentWidget() else \
            self.add_tag_input.mapToGlobal(anchor.bottomLeft())
        api_rect = QRect(global_point, anchor.size())
        api_rect.setHeight(0)
        self._autocomplete_popup.show_suggestions(merged, api_rect)

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
            if tag not in self.tag_order:
                self.tag_order.append(tag)
            self.add_tag_input.clear()
            self._on_category_changed()
            self.update_preview()
            self._save_categories()

    def _show_tag_context_menu(self, pos):
        item = self.tag_list.itemAt(pos)
        if not item:
            return
        selected = self.tag_list.selectedItems()
        if not selected or item not in selected:
            selected = [item]
        tags = [it.text() for it in selected]
        current_cat = self.category_combo.currentText()
        menu = QMenu()
        label = f"Move {len(tags)} Selected to" if len(tags) > 1 else "Move to"
        move_menu = menu.addMenu(label)
        for cat in self.category_order:
            if cat == current_cat:
                continue
            act = move_menu.addAction(cat)
            act.setData(cat)
        move_menu.triggered.connect(lambda act: self._move_tags(tags, current_cat, act.data()))
        menu.addSeparator()
        remove_label = f"Remove {len(tags)} Selected" if len(tags) > 1 else "Remove"
        remove_act = menu.addAction(remove_label)
        remove_act.triggered.connect(lambda: self._remove_single_tags(tags, current_cat))
        menu.exec_(self.tag_list.mapToGlobal(pos))

    def _rename_tag(self, old_tag, new_tag):
        """Rename a tag everywhere it exists: in whichever category holds
        it (in place, same list position) and in the global flat prompt
        order (same position). If the new name collides with a tag that
        already exists in the same place, the old one is dropped instead
        of creating a duplicate."""
        if old_tag == new_tag or not new_tag:
            return
        for cat, tags in self.categories.items():
            if old_tag in tags:
                idx = tags.index(old_tag)
                if new_tag in tags:
                    del tags[idx]
                else:
                    tags[idx] = new_tag
        if old_tag in self.tag_order:
            idx = self.tag_order.index(old_tag)
            if new_tag in self.tag_order:
                del self.tag_order[idx]
            else:
                self.tag_order[idx] = new_tag

    def _apply_find_replace(self):
        find_pattern = self.find_input.text()
        replace_pattern = self.replace_input.text()
        if not find_pattern:
            return

        pattern = find_pattern if self.regex_check.isChecked() else re.escape(find_pattern)
        try:
            re.compile(pattern)
        except re.error as e:
            QMessageBox.warning(self, "Invalid Pattern", f"'{find_pattern}' is not a valid regular expression:\n{e}")
            return

        old_tags = list(self.tag_order)
        new_tags = AdvancedBulkOperations.apply_regex_find_replace(old_tags, pattern, replace_pattern)

        renamed = 0
        for old_tag, new_tag in zip(old_tags, new_tags):
            if new_tag != old_tag:
                self._rename_tag(old_tag, new_tag)
                renamed += 1

        if renamed:
            self._on_category_changed()
            self.update_preview()
            self._save_categories()
            QMessageBox.information(self, "Find & Replace", f"Updated {renamed} tag(s).")
        else:
            QMessageBox.information(self, "Find & Replace", "No tags matched.")

    def _open_reorder_dialog(self):
        flat = self._get_flat_order()
        if not flat:
            QMessageBox.information(self, "Reorder Words", "There are no tags to reorder yet.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Reorder Prompt Words")
        dialog.resize(420, 500)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Drag tags up/down to change their order in the prompt:"))

        order_list = QListWidget()
        order_list.setDragDropMode(QListWidget.InternalMove)
        order_list.setDefaultDropAction(Qt.MoveAction)
        for tag in flat:
            order_list.addItem(QListWidgetItem(tag))
        layout.addWidget(order_list)

        def _refill(new_tags):
            order_list.clear()
            for t in new_tags:
                order_list.addItem(QListWidgetItem(t))

        sort_row = QHBoxLayout()
        az_btn = QPushButton("A → Z")
        za_btn = QPushButton("Z → A")
        len_btn = QPushButton("By Length")
        reset_btn = QPushButton("Reset")
        for b in (az_btn, za_btn, len_btn, reset_btn):
            sort_row.addWidget(b)
        layout.addLayout(sort_row)

        az_btn.clicked.connect(lambda: _refill(AdvancedBulkOperations.apply_sort_tags(
            [order_list.item(i).text() for i in range(order_list.count())], "alphabetical")))
        za_btn.clicked.connect(lambda: _refill(AdvancedBulkOperations.apply_sort_tags(
            [order_list.item(i).text() for i in range(order_list.count())], "reverse")))
        len_btn.clicked.connect(lambda: _refill(AdvancedBulkOperations.apply_sort_tags(
            [order_list.item(i).text() for i in range(order_list.count())], "by_length")))
        reset_btn.clicked.connect(lambda: _refill(flat))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() == QDialog.Accepted:
            new_order = [order_list.item(i).text() for i in range(order_list.count())]
            if sorted(new_order) == sorted(flat):
                self.tag_order = new_order
                self.update_preview()
                self._save_categories()
            else:
                QMessageBox.warning(self, "Reorder Words", "Reordering was not applied due to an unexpected mismatch.")

    def _move_tags(self, tags, from_cat, to_cat):
        moved = 0
        for tag in tags:
            if from_cat in self.categories and tag in self.categories[from_cat]:
                self.categories[from_cat].remove(tag)
                moved += 1
        if to_cat not in self.categories:
            self.categories[to_cat] = []
        for tag in tags:
            if tag not in self.categories[to_cat]:
                self.categories[to_cat].append(tag)
        if moved:
            self._on_category_changed()
            self.update_preview()
            self._save_categories()

    def _prune_tag_order(self, removed_tags):
        """Drop tags from the global flat order once they no longer appear
        in any category (a tag moved between categories is never pruned,
        since it's still present somewhere)."""
        still_present = set()
        for cat_tags in self.categories.values():
            still_present.update(cat_tags)
        removed_set = set(removed_tags)
        self.tag_order = [t for t in self.tag_order if t in still_present or t not in removed_set]

    def _remove_single_tags(self, tags, from_cat):
        if from_cat in self.categories:
            self.categories[from_cat] = [t for t in self.categories[from_cat] if t not in tags]
            self._prune_tag_order(tags)
            self._on_category_changed()
            self.update_preview()
            self._save_categories()

    def _remove_selected_tags(self):
        current_cat = self.category_combo.currentText()
        selected = self.tag_list.selectedItems()
        if selected:
            to_remove = [item.text() for item in selected]
            if current_cat in self.categories:
                self.categories[current_cat] = [t for t in self.categories[current_cat] if t not in to_remove]
                self._prune_tag_order(to_remove)
                self._on_category_changed()
                self.update_preview()
                self._save_categories()

    def _clear_category(self):
        current_cat = self.category_combo.currentText()
        if current_cat in self.categories and self.categories[current_cat]:
            if QMessageBox.question(self, "Clear Category", f"Clear all tags in '{current_cat}'?") == QMessageBox.Yes:
                removed = self.categories[current_cat].copy()
                self.categories[current_cat].clear()
                self._prune_tag_order(removed)
                self._on_category_changed()
                self.update_preview()
                self._save_categories()

    def clear_all(self):
        if QMessageBox.question(self, "Clear All", "Clear all tags from all categories?") == QMessageBox.Yes:
            for cat in self.categories:
                self.categories[cat].clear()
            self.tag_order = []
            self._on_category_changed()
            self.update_preview()
            self._save_categories()

    def _json_path(self):
        return Path(__file__).parent.parent / "prompt_categories.json"

    def _path_to_key(self, path):
        """Normalize an image path (str or Path) into a stable dict key."""
        if not path:
            return None
        return str(Path(path))

    def load_categories(self):
        """Load the on-disk store. The store holds one categories dict per
        image (keyed by path) plus a single shared category order."""
        json_path = self._json_path()
        self._all_data = {'images': {}, 'order': DEFAULT_ORDER.copy()}

        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'images' in data:
                    self._all_data['images'] = data.get('images', {})
                    self._all_data['order'] = data.get('order', DEFAULT_ORDER.copy())
                else:
                    # Legacy single-state file from before per-image support.
                    # Preserve the old data instead of discarding it.
                    legacy_categories = data.get('categories', {})
                    self._all_data['order'] = data.get('order', DEFAULT_ORDER.copy())
                    if any(legacy_categories.get(cat) for cat in legacy_categories):
                        self._all_data['images']['__migrated_legacy_data__'] = legacy_categories
                    logger.info(
                        f"Migrated legacy single-state prompt_categories.json at {json_path} "
                        f"to per-image format (old data preserved under '__migrated_legacy_data__')"
                    )
                    self._save_all()
                logger.info(f"Loaded prompt categories from {json_path}")
            except Exception as e:
                logger.warning(f"Failed to load prompt categories: {e}")
        else:
            self._save_all()
            logger.info(f"Created new prompt categories store at {json_path}")

        self.category_order = self._all_data['order']
        self.category_combo.clear()
        self.category_combo.addItems(self.category_order)

        # No image selected yet; show an empty, unsaved scratch state until
        # set_current_image() is called.
        self.current_image_key = None
        self.categories = {cat: [] for cat in self.category_order}
        self.tag_order = []
        self._on_category_changed()

    def _derive_tag_order(self, categories):
        """Fallback for images saved before tag_order existed: reconstruct
        a starting order from current category order/list order."""
        order = []
        for cat in self.category_order:
            for tag in categories.get(cat, []):
                if tag not in order:
                    order.append(tag)
        # catch any tags in categories not covered by category_order
        for cat, tags in categories.items():
            for tag in tags:
                if tag not in order:
                    order.append(tag)
        return order

    def set_current_image(self, path):
        """Switch the Prompt Builder to show/edit the state for a specific
        image. Pass None/falsy to clear to an unsaved scratch state (e.g.
        when no image is loaded)."""
        key = self._path_to_key(path)
        self.current_image_key = key

        if key is None:
            self.categories = {cat: [] for cat in self.category_order}
            self.tag_order = []
        else:
            stored = self._all_data['images'].get(key)
            if stored is None:
                stored = {'categories': {cat: [] for cat in self.category_order}, 'tag_order': []}
                self._all_data['images'][key] = stored
            elif 'categories' not in stored:
                # Backward compat: earlier per-image format was just a flat
                # {category: [tags]} dict with no separate tag_order.
                old_categories = stored
                stored = {
                    'categories': old_categories,
                    'tag_order': self._derive_tag_order(old_categories),
                }
                self._all_data['images'][key] = stored

            for cat in self.category_order:
                stored['categories'].setdefault(cat, [])
            stored.setdefault('tag_order', self._derive_tag_order(stored['categories']))

            self.categories = stored['categories']
            self.tag_order = stored['tag_order']

        self.add_tag_input.clear()
        self._on_category_changed()
        self.update_preview()

    def _save_all(self):
        json_path = self._json_path()
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self._all_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save prompt categories: {e}")

    def _save_categories(self):
        if self.current_image_key is not None:
            self._all_data['images'][self.current_image_key] = {
                'categories': self.categories,
                'tag_order': self.tag_order,
            }
        self._all_data['order'] = self.category_order
        self._save_all()

    def _get_tag_category(self, tag: str):
        """Look up a tag's Danbooru category from the tag DB."""
        if not self.tag_db or not self.tag_db.is_loaded:
            return None
        results = self.tag_db.search(tag, limit=1)
        if results and results[0]['name'].lower() == tag.lower():
            return results[0].get('category', 0)
        return None

    def _classify_general(self, tag_name: str):
        """Classify a general (category 0) tag into a sub-category using keyword scoring."""
        name = tag_name.lower().replace('_', ' ').replace('-', ' ')

        best_cat = None
        best_score = 0

        for section, keywords in GENERAL_KEYWORD_MAP.items():
            score = 0
            for kw in keywords:
                if kw in name:
                    score += len(kw)
            if score > best_score:
                best_score = score
                best_cat = section

        return best_cat if best_score > 0 else None

    def seed_from_tags(self, tags):
        """
        Import tags from the image. Behavior depends on self.replace_check.
        - If checked: clear all categories, then add the image's tags.
        - If unchecked: merge the image's tags with existing categories (no duplicates).
        """
        if self.replace_check.isChecked():
            # Replace mode: clear everything first
            for cat in self.categories:
                self.categories[cat].clear()
            # Ensure all categories exist
            for cat in self.category_order:
                if cat not in self.categories:
                    self.categories[cat] = []
            self.tag_order = []
            stats = defaultdict(int)
            added_count = 0
            for tag in tags:
                db_cat = self._get_tag_category(tag)
                target = None
                if db_cat == 1:
                    target = "Artist"
                elif db_cat == 3:
                    target = "Copyright"
                elif db_cat == 4:
                    target = "Character"
                elif db_cat == 5:
                    target = "Meta"
                else:
                    target = self._classify_general(tag)
                    if target is None:
                        target = "Uncategorized"
                if target in self.categories:
                    self.categories[target].append(tag)
                else:
                    self.categories.setdefault("Uncategorized", []).append(tag)
                    target = "Uncategorized"
                if tag not in self.tag_order:
                    self.tag_order.append(tag)
                stats[target] += 1
                added_count += 1
            if added_count:
                self._on_category_changed()
                self.update_preview()
                self._save_categories()
            total = len(tags)
            parts = [f"Replaced with {added_count} tags from {total}"]
            classified = sum(v for k, v in stats.items() if k != "Uncategorized")
            if classified:
                parts.append(f"{classified} classified")
            if stats.get("Uncategorized", 0):
                parts.append(f"{stats['Uncategorized']} unclassified")
            self.grouping_completed.emit(" \u00b7 ".join(parts))
            return added_count

        else:
            # Merge mode: only add tags that don't already exist anywhere
            # Ensure all categories exist
            for cat in self.category_order:
                if cat not in self.categories:
                    self.categories[cat] = []
            stats = defaultdict(int)
            added_count = 0
            # Build a set of all existing tags for quick lookup
            existing_tags = set()
            for cat in self.categories:
                existing_tags.update(self.categories[cat])

            for tag in tags:
                if tag in existing_tags:
                    stats["already_present"] += 1
                    continue
                db_cat = self._get_tag_category(tag)
                target = None
                if db_cat == 1:
                    target = "Artist"
                elif db_cat == 3:
                    target = "Copyright"
                elif db_cat == 4:
                    target = "Character"
                elif db_cat == 5:
                    target = "Meta"
                else:
                    target = self._classify_general(tag)
                    if target is None:
                        target = "Uncategorized"
                if target in self.categories:
                    self.categories[target].append(tag)
                else:
                    self.categories.setdefault("Uncategorized", []).append(tag)
                    target = "Uncategorized"
                if tag not in self.tag_order:
                    self.tag_order.append(tag)
                stats[target] += 1
                added_count += 1
                existing_tags.add(tag)  # avoid duplicate within the same batch

            if added_count:
                self._on_category_changed()
                self.update_preview()
                self._save_categories()

            total = len(tags)
            parts = [f"Merged {added_count} new tags from {total}"]
            if stats.get("already_present", 0):
                parts.append(f"{stats['already_present']} already present")
            classified = sum(v for k, v in stats.items() if k not in ("Uncategorized", "already_present"))
            if classified:
                parts.append(f"{classified} classified")
            if stats.get("Uncategorized", 0):
                parts.append(f"{stats['Uncategorized']} unclassified")
            self.grouping_completed.emit(" \u00b7 ".join(parts))
            return added_count

    def _get_flat_order(self):
        """Tags in their original/global order, independent of which
        category they currently belong to. This is what moving a tag
        between categories should NOT change."""
        all_tags = set()
        for cat_tags in self.categories.values():
            all_tags.update(cat_tags)

        flat = [t for t in self.tag_order if t in all_tags]

        # Safety net: include any tag present in a category but missing
        # from tag_order (shouldn't normally happen, but keeps nothing lost)
        seen = set(flat)
        for cat in self.category_order:
            for t in self.categories.get(cat, []):
                if t not in seen:
                    flat.append(t)
                    seen.add(t)
        return flat

    def update_preview(self):
        format_mode = self.format_combo.currentText()
        include_negative = self.include_negative.isChecked()

        if format_mode == "Grouped by Category":
            ordered = []
            for cat in self.category_order:
                if cat in self.categories and self.categories[cat]:
                    ordered.append((cat, self.categories[cat]))
            sections = []
            for cat, tags in ordered:
                sections.append(f"### {cat}")
                sections.extend(tags)
                sections.append("")
            prompt = "\n".join(sections)
        else:
            flat = self._get_flat_order()
            if format_mode == "Multi-Line":
                prompt = "\n".join(flat)
            else:  # Comma Separated or Compact
                prompt = ", ".join(flat)

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