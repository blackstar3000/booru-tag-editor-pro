# core/navigation_controller.py
"""
NavigationController – single source of truth for folder navigation.
"""

from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
import random
import logging

logger = logging.getLogger(__name__)

class NavigationController(QObject):
    # Signals
    folder_loaded = pyqtSignal(str)               # folder path
    image_list_changed = pyqtSignal(list)         # list of Path objects
    current_image_changed = pyqtSignal(str, int)  # path, index
    sort_order_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.current_folder = None
        self.image_paths = []
        self.current_index = -1
        self.sort_order = "name"      # name, date, size, random
        self.filter_pattern = ""      # future use (e.g., "*.png")
        self._last_viewed = {}        # folder_path -> index

    def load_folder(self, folder_path):
        """Set the active folder and scan its contents."""
        self.current_folder = str(Path(folder_path))
        self._scan_folder()
        self.folder_loaded.emit(self.current_folder)
        # Restore last viewed index if available
        idx = self._last_viewed.get(self.current_folder, 0)
        self.set_current_index(idx)

    def _scan_folder(self):
        """Populate image_paths based on current filter and sort."""
        if not self.current_folder:
            self.image_paths = []
            return
        folder = Path(self.current_folder)
        exts = ('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif')
        self.image_paths = [p for p in folder.glob("*") if p.suffix.lower() in exts]
        self.image_paths = self._apply_filter(self.image_paths)
        self.image_paths = self._apply_sort(self.image_paths)
        self.image_list_changed.emit(self.image_paths)

    def _apply_filter(self, paths):
        # Placeholder – future implementation
        return paths

    def _apply_sort(self, paths):
        if self.sort_order == "name":
            return sorted(paths, key=lambda p: p.name.lower())
        elif self.sort_order == "date":
            return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
        elif self.sort_order == "size":
            return sorted(paths, key=lambda p: p.stat().st_size, reverse=True)
        elif self.sort_order == "random":
            shuffled = paths.copy()
            random.shuffle(shuffled)
            return shuffled
        return paths

    def set_current_index(self, index):
        if not self.image_paths:
            self.current_index = -1
            self.current_image_changed.emit("", -1)
            return
        if index < 0:
            index = 0
        if index >= len(self.image_paths):
            index = len(self.image_paths) - 1
        if index != self.current_index:
            self.current_index = index
            if self.current_folder:
                self._last_viewed[self.current_folder] = index
            path = self.image_paths[index] if index >= 0 else None
            self.current_image_changed.emit(str(path) if path else "", index)

    def navigate(self, delta):
        """Move current index by delta (e.g., -1 or +1)."""
        if not self.image_paths:
            return
        new_idx = self.current_index + delta
        if 0 <= new_idx < len(self.image_paths):
            self.set_current_index(new_idx)

    def set_sort_order(self, order):
        if order != self.sort_order:
            self.sort_order = order
            self.sort_order_changed.emit(order)
            self._scan_folder()
            if self.image_paths:
                self.set_current_index(0)

    def refresh(self):
        """Rescan the current folder."""
        if self.current_folder:
            self._scan_folder()
            if self.current_index >= len(self.image_paths):
                self.set_current_index(len(self.image_paths)-1)
            else:
                self.set_current_index(self.current_index)