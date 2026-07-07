from PyQt5.QtCore import QObject, pyqtSignal
import logging
from typing import List

logger = logging.getLogger(__name__)

class TagManager(QObject):
    tags_changed = pyqtSignal(list)
    dirty_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._tags: List[str] = []
        self._undo_stack: List[List[str]] = []
        self._redo_stack: List[List[str]] = []
        self._max_history = 30
        self._dirty = False

    @property
    def tags(self) -> List[str]:
        return self._tags.copy()

    @property
    def dirty(self) -> bool:
        return self._dirty

    def load_tags(self, new_tags: List[str]):
        """Load tags from file (does not mark as dirty)."""
        self._tags = new_tags.copy()
        self._set_dirty(False)
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._log_state()
        self.tags_changed.emit(self._tags.copy())

    def set_tags(self, new_tags: List[str]):
        """Set tags as a result of user action (marks as dirty)."""
        self._push_state()
        self._tags = new_tags.copy()
        self._set_dirty(True)
        self._redo_stack.clear()
        self._log_state()
        self.tags_changed.emit(self._tags.copy())

    def add_tag(self, tag: str):
        if tag not in self._tags:
            self._push_state()
            self._tags.append(tag)
            self._set_dirty(True)
            self._redo_stack.clear()
            self._log_state()
            self.tags_changed.emit(self._tags.copy())

    def remove_tag(self, tag: str):
        if tag in self._tags:
            self._push_state()
            self._tags.remove(tag)
            self._set_dirty(True)
            self._redo_stack.clear()
            self._log_state()
            self.tags_changed.emit(self._tags.copy())

    def remove_tags(self, tags: List[str]):
        self._push_state()
        for tag in tags:
            if tag in self._tags:
                self._tags.remove(tag)
        self._set_dirty(True)
        self._redo_stack.clear()
        self._log_state()
        self.tags_changed.emit(self._tags.copy())

    def reorder_tags(self, new_order: List[str]):
        self._push_state()
        self._tags = new_order.copy()
        self._set_dirty(True)
        self._redo_stack.clear()
        self._log_state()
        self.tags_changed.emit(self._tags.copy())

    def undo(self) -> bool:
        if not self._undo_stack:
            return False
        self._redo_stack.append(self._tags.copy())
        self._tags = self._undo_stack.pop()
        self._set_dirty(True)
        self._log_state()
        self.tags_changed.emit(self._tags.copy())
        return True

    def redo(self) -> bool:
        if not self._redo_stack:
            return False
        self._undo_stack.append(self._tags.copy())
        self._tags = self._redo_stack.pop()
        self._set_dirty(True)
        self._log_state()
        self.tags_changed.emit(self._tags.copy())
        return True

    def save(self) -> List[str]:
        self._set_dirty(False)
        return self._tags.copy()

    def _push_state(self):
        self._undo_stack.append(self._tags.copy())
        if len(self._undo_stack) > self._max_history:
            self._undo_stack.pop(0)

    def _set_dirty(self, val: bool):
        if self._dirty != val:
            self._dirty = val
            self.dirty_changed.emit(val)

    def _log_state(self):
        logger.debug(f"Tags: {self._tags} (dirty={self._dirty})")