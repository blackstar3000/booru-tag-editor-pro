"""
Modern Glassmorphism Tooltip System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
A reusable, animated, rich-content tooltip framework that matches
the application's dark purple glassmorphism aesthetic.

Usage:
    from ui.tooltips import attach_tooltip, TooltipManager

    attach_tooltip(my_button, title="Save", description="Save all edits.", icon="💾", shortcut="Ctrl+S")

    # Batch registration
    TooltipManager.register({
        button_a: {"title": "Action A", "description": "Does A."},
        button_b: {"title": "Action B", "description": "Does B.", "shortcut": "Ctrl+B"},
    })
"""

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QApplication
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QRect, pyqtProperty, QRectF, QEvent, QObject
)
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPolygon, QPainterPath


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Theme Definitions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VARIANTS = {
    "default": {
        "accent": "#8B5CF6",
        "accent_rgb": (139, 92, 246),
        "glow": "rgba(145, 90, 255, .20)",
        "border": "rgba(170, 120, 255, .35)",
        "icon_color": "#B48AFF",
    },
    "info": {
        "accent": "#3B82F6",
        "accent_rgb": (59, 130, 246),
        "glow": "rgba(59, 130, 246, .20)",
        "border": "rgba(96, 165, 250, .35)",
        "icon_color": "#60A5FA",
    },
    "success": {
        "accent": "#22C55E",
        "accent_rgb": (34, 197, 94),
        "glow": "rgba(34, 197, 94, .20)",
        "border": "rgba(74, 222, 128, .35)",
        "icon_color": "#4ADE80",
    },
    "warning": {
        "accent": "#F59E0B",
        "accent_rgb": (245, 158, 11),
        "glow": "rgba(245, 158, 11, .18)",
        "border": "rgba(251, 191, 36, .35)",
        "icon_color": "#FBBF24",
    },
    "error": {
        "accent": "#EF4444",
        "accent_rgb": (239, 68, 68),
        "glow": "rgba(239, 68, 68, .20)",
        "border": "rgba(248, 113, 113, .35)",
        "icon_color": "#F87171",
    },
    "ai": {
        "accent": "#EC4899",
        "accent_rgb": (236, 72, 153),
        "glow": "rgba(236, 72, 153, .20)",
        "border": "rgba(244, 114, 182, .35)",
        "icon_color": "#F472B6",
    },
}

POINTER_SIZE = 8
CORNER_RADIUS = 14
TOOLTIP_MAX_WIDTH = 340
HOVER_DELAY_MS = 300
ANIM_DURATION_MS = 180


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tooltip Window
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TooltipWindow(QWidget):
    """A single reusable floating tooltip window with pointer, animations,
    and rich content support."""

    def __init__(self, parent=None):
        # Use Qt.ToolTip instead of Popup – stays on top, doesn't steal focus,
        # and won't auto‑close on mouse movement.
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)  # mouse events pass through
        self.setMouseTracking(True)

        self._opacity = 0.0
        self._variant = "default"
        self._pointer_side = "bottom"
        self._pointer_x = 0

        # ── Content layout ────────────────────────────────────────
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(20, 16, 20, 16)
        self._content_layout.setSpacing(6)
        self._main_layout.addWidget(self._content_widget)

        # Header row: icon + title
        self._header_row = QHBoxLayout()
        self._header_row.setSpacing(8)
        self._header_row.setContentsMargins(0, 0, 0, 0)

        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setFixedWidth(24)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        self._header_row.addWidget(self._icon_label)

        self._title_label = QLabel()
        self._title_label.setWordWrap(True)
        self._title_label.setStyleSheet("background: transparent; border: none;")
        self._header_row.addWidget(self._title_label, 1)

        self._content_layout.addLayout(self._header_row)

        # Description
        self._desc_label = QLabel()
        self._desc_label.setWordWrap(True)
        self._desc_label.setMaximumWidth(TOOLTIP_MAX_WIDTH - 40)
        self._desc_label.setStyleSheet("background: transparent; border: none;")
        self._content_layout.addWidget(self._desc_label)

        # Divider
        self._divider = QWidget()
        self._divider.setFixedHeight(1)
        self._divider.setStyleSheet("background: rgba(255,255,255,0.06); border: none; margin: 4px 0;")
        self._content_layout.addWidget(self._divider)

        # Footer row: shortcut badge
        self._footer_row = QHBoxLayout()
        self._footer_row.setContentsMargins(0, 0, 0, 0)
        self._footer_row.setSpacing(6)

        self._shortcut_label = QLabel()
        self._shortcut_label.setStyleSheet("background: transparent; border: none;")
        self._footer_row.addWidget(self._shortcut_label)

        self._footer_row.addStretch()
        self._content_layout.addLayout(self._footer_row)

        # Fade-in animation
        self._fade_anim = QPropertyAnimation(self, b"tooltipOpacity")
        self._fade_anim.setDuration(ANIM_DURATION_MS)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    # ── Prevent window from being deleted on close ────────────────────
    def closeEvent(self, event):
        """Override close event: hide the window and ignore the close
        to prevent deletion."""
        self.hide()
        event.ignore()

    # ── Opacity property for animation ─────────────────────────────

    def _get_opacity(self):
        return self._opacity

    def _set_opacity(self, val):
        self._opacity = val
        self.setWindowOpacity(val)

    tooltipOpacity = pyqtProperty(float, fget=_get_opacity, fset=_set_opacity)

    # ── Content setters ───────────────────────────────────────────

    def set_content(self, title="", description="", icon="", shortcut="", variant="default"):
        self._variant = variant if variant in VARIANTS else "default"
        v = VARIANTS[self._variant]

        # Icon
        if icon:
            self._icon_label.setText(icon)
            self._icon_label.setFixedWidth(24)
            self._icon_label.show()
        else:
            self._icon_label.hide()

        # Title
        if title:
            self._title_label.setText(title)
            self._title_label.setStyleSheet(
                f"background: transparent; border: none; color: {v['accent']}; "
                f"font-size: 14pt; font-weight: bold;"
            )
            self._title_label.show()
        else:
            self._title_label.hide()

        # Description
        if description:
            self._desc_label.setText(description)
            self._desc_label.setStyleSheet(
                "background: transparent; border: none; color: #ccc; font-size: 11pt; "
                "line-height: 140%;"
            )
            self._desc_label.setMaximumWidth(TOOLTIP_MAX_WIDTH - 40)
            self._desc_label.show()
        else:
            self._desc_label.hide()

        # Divider
        has_footer = bool(shortcut)
        self._divider.setVisible(bool(title and description) or has_footer)

        # Shortcut badge
        if shortcut:
            badge_html = (
                f'<span style="background: rgba(20,22,30,0.9); '
                f'border: 1px solid {v["border"]}; '
                f'border-radius: 6px; padding: 3px 10px; '
                f'color: {v["accent"]}; font-size: 10pt; '
                f'font-family: Segoe UI, sans-serif;">'
                f'{shortcut}</span>'
            )
            self._shortcut_label.setText(badge_html)
            self._shortcut_label.show()
        else:
            self._shortcut_label.hide()

        # Footer row visibility
        self._footer_row.setAlignment(Qt.AlignLeft)
        for i in range(self._footer_row.count()):
            item = self._footer_row.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(bool(shortcut))

        self.adjustSize()

    # ── Painting (background + pointer) ───────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        v = VARIANTS[self._variant]
        bg = QColor(17, 17, 24, 242)
        border_col = QColor(*v["accent_rgb"], 89)
        glow_col = QColor(*v["accent_rgb"], 51)

        w, h = self.width(), self.height()
        ps = POINTER_SIZE

        if self._pointer_side == "bottom":
            rect = QRectF(0, 0, w, h - ps)
        elif self._pointer_side == "top":
            rect = QRectF(0, ps, w, h - ps)
        elif self._pointer_side == "right":
            rect = QRectF(0, 0, w - ps, h)
        else:
            rect = QRectF(ps, 0, w - ps, h)

        r = CORNER_RADIUS
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        # Manual shadow: concentric rects with decreasing alpha
        shadow_steps = 12
        for i in range(shadow_steps, 0, -1):
            spread = i * 1.5
            alpha = max(0, 60 - i * 5)
            if alpha <= 0:
                continue
            sr = rect.translated(0, 8 + spread * 0.3).adjusted(-spread, -spread, spread, spread)
            sp = QPainterPath()
            sp.addRoundedRect(sr, r + spread * 0.3, r + spread * 0.3)
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.setPen(Qt.NoPen)
            painter.drawPath(sp)

        # Glow layer
        painter.setBrush(glow_col)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Background
        painter.setBrush(bg)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # Border
        painter.setBrush(Qt.NoBrush)
        painter.setPen(border_col)
        painter.drawPath(path)

        # Pointer triangle
        tip = self._pointer_tip()
        if tip:
            painter.setPen(Qt.NoPen)
            painter.setBrush(bg)
            painter.drawPolygon(tip)
            painter.setPen(border_col)
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(tip)

        painter.end()

    def _pointer_tip(self):
        ps = POINTER_SIZE
        w, h = self.width(), self.height()
        px = self._pointer_x

        if self._pointer_side == "bottom":
            return QPolygon([
                QPoint(int(px - ps), h - ps),
                QPoint(int(px), h),
                QPoint(int(px + ps), h - ps),
            ])
        elif self._pointer_side == "top":
            return QPolygon([
                QPoint(int(px - ps), ps),
                QPoint(int(px), 0),
                QPoint(int(px + ps), ps),
            ])
        elif self._pointer_side == "right":
            return QPolygon([
                QPoint(w - ps, int(px - ps)),
                QPoint(w, int(px)),
                QPoint(w - ps, int(px + ps)),
            ])
        else:
            return QPolygon([
                QPoint(ps, int(px - ps)),
                QPoint(0, int(px)),
                QPoint(ps, int(px + ps)),
            ])

    # ── Show / Hide with animation ────────────────────────────────

    def fade_in(self):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        self.show()
        self.raise_()  # ensure it's on top

    def fade_out(self):
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity)
        self._fade_anim.setEndValue(0.0)
        # Disconnect any previous finished connections to avoid duplicates
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_done)
        except TypeError:
            pass
        self._fade_anim.finished.connect(self._on_fade_out_done)
        self._fade_anim.start()

    def _on_fade_out_done(self):
        self.hide()
        try:
            self._fade_anim.finished.disconnect(self._on_fade_out_done)
        except TypeError:
            pass

    # ── Position calculation ──────────────────────────────────────

    def position_for(self, widget, preferred_side="bottom"):
        """Calculate the best position for the tooltip relative to *widget*.
        Returns (pos QPoint, pointer_side str, pointer_x float)."""
        geo = widget.geometry()
        w_pos = widget.mapToGlobal(QPoint(0, 0))
        screen = widget.screen().availableGeometry()

        self.adjustSize()
        tw, th = self.width(), self.height()

        # Try preferred side first, then alternatives
        sides = [preferred_side]
        if preferred_side == "bottom":
            sides += ["top", "right", "left"]
        elif preferred_side == "top":
            sides += ["bottom", "right", "left"]
        elif preferred_side == "right":
            sides += ["left", "bottom", "top"]
        else:
            sides += ["right", "bottom", "top"]

        ps = POINTER_SIZE
        for side in sides:
            if side == "bottom":
                # Tooltip below widget – pointer should be at the top of the tooltip
                x = w_pos.x() + geo.width() // 2 - tw // 2
                y = w_pos.y() + geo.height() + ps
                ptr_x = tw // 2
                pointer_side = "top"
            elif side == "top":
                # Tooltip above widget – pointer should be at the bottom of the tooltip
                x = w_pos.x() + geo.width() // 2 - tw // 2
                y = w_pos.y() - th - ps
                ptr_x = tw // 2
                pointer_side = "bottom"
            elif side == "right":
                # Tooltip to the right – pointer on the left
                x = w_pos.x() + geo.width() + ps
                y = w_pos.y() + geo.height() // 2 - th // 2
                ptr_x = th // 2
                pointer_side = "left"
            else:  # left
                # Tooltip to the left – pointer on the right
                x = w_pos.x() - tw - ps
                y = w_pos.y() + geo.height() // 2 - th // 2
                ptr_x = th // 2
                pointer_side = "right"

            # Clamp to screen
            if x < screen.left() + 4:
                x = screen.left() + 4
            elif x + tw > screen.right() - 4:
                x = screen.right() - tw - 4
            if y < screen.top() + 4:
                y = screen.top() + 4
            elif y + th > screen.bottom() - 4:
                continue

            return QPoint(x, y), pointer_side, float(ptr_x)

        # Fallback: place below and clamp
        x = w_pos.x() + geo.width() // 2 - tw // 2
        y = w_pos.y() + geo.height() + ps
        x = max(screen.left() + 4, min(x, screen.right() - tw - 4))
        y = max(screen.top() + 4, min(y, screen.bottom() - th - 4))
        return QPoint(x, y), "top", float(tw // 2)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tooltip Manager (Singleton)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class _WidgetEventFilter(QObject):
    """Event filter installed on each registered widget."""
    def __init__(self, widget, parent=None):
        super().__init__(parent)
        self._widget = widget

    def eventFilter(self, obj, event):
        if obj is not self._widget:
            return False
        if event.type() == QEvent.Enter:
            TooltipManager._on_enter(self._widget)
        elif event.type() == QEvent.Leave:
            TooltipManager._on_leave(self._widget)
        elif event.type() == QEvent.ToolTip:
            # Suppress native tooltips
            return True
        return False


class TooltipManager:
    """Singleton that manages tooltip lifecycle, timers, and per‑widget event filters."""

    _instance = None
    _window: TooltipWindow = None
    _hover_timer: QTimer = None
    _active_widget = None
    _configs: dict = {}
    _filters: dict = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def _ensure_initialized(cls):
        if cls._window is None:
            cls._window = TooltipWindow()
            cls._hover_timer = QTimer()
            cls._hover_timer.setSingleShot(True)
            cls._hover_timer.timeout.connect(cls._show_tooltip)

    @classmethod
    def register(cls, widget, config=None, **kwargs):
        """Register a tooltip for a widget. Accepts either a config dict
        or keyword arguments."""
        cls._ensure_initialized()

        if config is None:
            config = kwargs

        # Remove any existing filter for this widget
        if widget in cls._filters:
            widget.removeEventFilter(cls._filters[widget])
            del cls._filters[widget]

        cls._configs[widget] = config

        # Install a dedicated event filter on the widget
        filter_obj = _WidgetEventFilter(widget)
        widget.installEventFilter(filter_obj)
        cls._filters[widget] = filter_obj

    @classmethod
    def unregister(cls, widget):
        """Remove a tooltip from a widget."""
        if widget in cls._filters:
            widget.removeEventFilter(cls._filters[widget])
            del cls._filters[widget]
        cls._configs.pop(widget, None)

    @classmethod
    def register_batch(cls, mapping: dict):
        """Register multiple widgets at once.
        mapping: {widget: {title, description, icon, shortcut, variant}, ...}"""
        for widget, config in mapping.items():
            cls.register(widget, config)

    @classmethod
    def _show_tooltip(cls):
        if cls._active_widget is None or cls._active_widget not in cls._configs:
            return
        config = cls._configs[cls._active_widget]
        cls._window.set_content(
            title=config.get("title", ""),
            description=config.get("description", ""),
            icon=config.get("icon", ""),
            shortcut=config.get("shortcut", ""),
            variant=config.get("variant", "default"),
        )
        pos, side, ptr_x = cls._window.position_for(
            cls._active_widget,
            preferred_side=config.get("position", "bottom"),
        )
        cls._window._pointer_side = side
        cls._window._pointer_x = ptr_x
        cls._window.move(pos)
        cls._window.fade_in()

    @classmethod
    def _hide_tooltip(cls):
        cls._hover_timer.stop()
        if cls._window and cls._window.isVisible():
            cls._window.fade_out()
        cls._active_widget = None

    @classmethod
    def _on_enter(cls, widget):
        cls._active_widget = widget
        cls._hover_timer.start(HOVER_DELAY_MS)

    @classmethod
    def _on_leave(cls, widget):
        if cls._active_widget == widget:
            cls._hide_tooltip()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Public Helpers
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def attach_tooltip(widget, **kwargs):
    """Convenience: attach a tooltip to a single widget."""
    TooltipManager.register(widget, **kwargs)


def detach_tooltip(widget):
    """Remove a tooltip from a widget."""
    TooltipManager.unregister(widget)


def register_tooltips(mapping: dict):
    """Batch-register tooltips. See TooltipManager.register_batch."""
    TooltipManager.register_batch(mapping)