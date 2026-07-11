# ui/filmstrip.py
"""
Filmstrip – horizontal thumbnail strip for rapid image navigation.
Supports optional auto-hide: hides after a timeout when the mouse
is not hovering over it.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QListWidget, QListWidgetItem,
    QListView, QFrame, QLabel, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QEvent
from PyQt5.QtGui import QPixmap, QIcon, QCursor
from pathlib import Path
import logging

from core.image_loader import ImageLoader

logger = logging.getLogger(__name__)

AUTO_HIDE_DELAY_MS = 5000
PREVIEW_MAX_SIZE = 320
PREVIEW_GAP_PX = 10


class Filmstrip(QWidget):
    image_selected = pyqtSignal(str)  # emits full path to selected image

    def __init__(self, image_loader: ImageLoader, parent=None):
        super().__init__(parent)
        self.image_loader = image_loader
        self.current_index = -1
        self._suppress_row_signal = False

        # Auto-hide state
        self._auto_hide_enabled = False
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._auto_hide_timeout)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.list_widget = QListWidget()
        self.list_widget.setFlow(QListView.LeftToRight)
        self.list_widget.setWrapping(False)
        self.list_widget.setResizeMode(QListView.Adjust)
        self.list_widget.setIconSize(QSize(90, 90))
        self.list_widget.setGridSize(QSize(100, 100))
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.setMinimumHeight(100)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
            }
            QListWidget::item {
                background: rgba(255, 255, 255, 0.03);
                border-radius: 8px;
                padding: 3px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: rgba(139, 92, 246, 0.3);
                border: 2px solid rgba(139, 92, 246, 0.6);
                border-radius: 8px;
            }
            QListWidget::item:hover:!selected {
                background: rgba(255, 255, 255, 0.06);
            }
        """)

        self.list_widget.setFocusPolicy(Qt.StrongFocus)
        self.list_widget.currentRowChanged.connect(self._on_current_row_changed)

        # Hover preview: mouse tracking + itemEntered fires without needing
        # a button held down, and a viewport-level Leave event tells us
        # when to hide the popup again.
        self.list_widget.setMouseTracking(True)
        self.list_widget.itemEntered.connect(self._on_item_entered)
        self.list_widget.viewport().installEventFilter(self)

        self.scroll_area.setWidget(self.list_widget)
        layout.addWidget(self.scroll_area)

        self._preview_popup = QWidget(None, Qt.ToolTip | Qt.FramelessWindowHint)
        self._preview_popup.setStyleSheet(
            "background: rgba(20, 20, 26, 235); "
            "border: 1px solid rgba(255, 255, 255, 50); "
            "border-radius: 10px;"
        )
        popup_layout = QVBoxLayout(self._preview_popup)
        popup_layout.setContentsMargins(6, 6, 6, 6)
        popup_layout.setSpacing(4)
        self._preview_image_label = QLabel()
        self._preview_image_label.setAlignment(Qt.AlignCenter)
        popup_layout.addWidget(self._preview_image_label)
        self._preview_caption_label = QLabel()
        self._preview_caption_label.setAlignment(Qt.AlignCenter)
        self._preview_caption_label.setStyleSheet("color: #ccc; font-size: 11px;")
        popup_layout.addWidget(self._preview_caption_label)
        self._preview_popup.hide()

    # ── Auto-hide ───────────────────────────────────────────────────

    def set_auto_hide(self, enabled: bool):
        """Enable or disable the auto-hide behaviour."""
        self._auto_hide_enabled = enabled
        if enabled:
            self._start_auto_hide_timer()
        else:
            self._auto_hide_timer.stop()
            self.show()

    def auto_hide_enabled(self) -> bool:
        return self._auto_hide_enabled

    def _start_auto_hide_timer(self):
        if self._auto_hide_enabled and self.isVisible():
            self._auto_hide_timer.start(AUTO_HIDE_DELAY_MS)

    def _auto_hide_timeout(self):
        if self._auto_hide_enabled:
            self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if self._auto_hide_enabled:
            self._start_auto_hide_timer()

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._auto_hide_enabled:
            # Cursor is somewhere over the filmstrip - pause the countdown
            # for as long as it stays there.
            self._auto_hide_timer.stop()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if not self._auto_hide_enabled:
            return
        # QScrollArea/QListWidget fill this widget entirely, so Qt sends a
        # leaveEvent here the instant the cursor moves onto one of them -
        # even though it never actually left the filmstrip visually. Check
        # the real cursor position against our own bounds before treating
        # this as a genuine "moved away" and restarting the hide timer.
        if self.rect().contains(self.mapFromGlobal(QCursor.pos())):
            return
        self._auto_hide_timer.start(AUTO_HIDE_DELAY_MS)

    def hideEvent(self, event):
        super().hideEvent(event)
        self._preview_popup.hide()

    def eventFilter(self, obj, event):
        if obj is self.list_widget.viewport() and event.type() == QEvent.Leave:
            self._preview_popup.hide()
        return super().eventFilter(obj, event)

    # ── Hover preview ───────────────────────────────────────────────

    def _on_item_entered(self, item):
        path_str = item.data(Qt.UserRole) if item else None
        if not path_str:
            self._preview_popup.hide()
            return
        path = Path(path_str)
        pixmap = self.image_loader.get_pixmap(path)
        if pixmap is None:
            self._preview_popup.hide()
            return
        scaled = pixmap.scaled(
            PREVIEW_MAX_SIZE, PREVIEW_MAX_SIZE,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._preview_image_label.setPixmap(scaled)
        self._preview_caption_label.setText(path.name)
        self._preview_popup.adjustSize()
        self._position_preview_popup(item)
        self._preview_popup.show()

    def _position_preview_popup(self, item):
        item_rect = self.list_widget.visualItemRect(item)
        viewport = self.list_widget.viewport()
        item_top_left = viewport.mapToGlobal(item_rect.topLeft())

        popup_w = self._preview_popup.width()
        popup_h = self._preview_popup.height()

        x = item_top_left.x() + (item_rect.width() - popup_w) // 2
        y = item_top_left.y() - popup_h - PREVIEW_GAP_PX

        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            x = max(avail.left(), min(x, avail.right() - popup_w))
            if y < avail.top():
                # Not enough room above (e.g. filmstrip near top of screen) -
                # show it below the item instead.
                y = item_top_left.y() + item_rect.height() + PREVIEW_GAP_PX

        self._preview_popup.move(x, y)

    # ── Public helpers ──────────────────────────────────────────────

    def show_and_reset_timer(self):
        """Show the filmstrip and restart the hide timer (for external callers)."""
        self.show()
        if self._auto_hide_enabled:
            self._auto_hide_timer.start(AUTO_HIDE_DELAY_MS)

    def set_images(self, paths: list):
        """Populate the filmstrip with thumbnails."""
        self.list_widget.clear()
        self.current_index = -1
        if not paths:
            return
        for path in paths:
            pixmap = self.image_loader.get_pixmap(path)
            if pixmap is None:
                pixmap = QPixmap(100, 100)
                pixmap.fill(Qt.darkGray)
            scaled = pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(scaled)
            item = QListWidgetItem(icon, "")
            item.setData(Qt.UserRole, str(path))
            self.list_widget.addItem(item)
        # Select the first item if available
        if self.list_widget.count() > 0:
            self.set_current_index(0)

    def set_current_index(self, index: int):
        """Highlight the thumbnail at the given index (programmatic)."""
        if index < 0 or index >= self.list_widget.count():
            return
        self.current_index = index
        self._suppress_row_signal = True
        self.list_widget.setCurrentRow(index)
        self._suppress_row_signal = False
        self.list_widget.scrollToItem(self.list_widget.item(index), QListView.PositionAtCenter)

    def set_current_image(self, path: str):
        """Highlight the thumbnail matching the given path."""
        if not path:
            return
        for i in range(self.list_widget.count()):
            item_path = self.list_widget.item(i).data(Qt.UserRole)
            if item_path == path:
                self.set_current_index(i)
                return

    def navigate(self, delta: int):
        """Move selection by delta and emit the new image."""
        if self.list_widget.count() == 0:
            return
        new_index = self.current_index + delta
        if 0 <= new_index < self.list_widget.count():
            self.list_widget.setCurrentRow(new_index)  # triggers _on_current_row_changed

    def _on_current_row_changed(self, row):
        if self._suppress_row_signal or row < 0:
            return
        self.current_index = row
        self.list_widget.scrollToItem(self.list_widget.item(row), QListView.PositionAtCenter)
        item = self.list_widget.item(row)
        if item:
            path = item.data(Qt.UserRole)
            if path:
                self.image_selected.emit(path)