"""Shared animation and interaction utilities for Trackora's PySide6 GUI.

Provides lightweight, calibrated micro-interactions and transitions (120-180ms)
without altering the core visual identity or imposing runtime overhead.
"""

from __future__ import annotations

from typing import Callable, Sequence, TypeVar, Any
from PySide6.QtCore import (
    QEasingCurve, QObject, QPointF, QPropertyAnimation, QRectF,
    QSize, Qt, QVariantAnimation, Signal,
)
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect, QLayout, QStackedWidget, QWidget,
)

# ── Color Constants matching Trackora's visual identity ──────────────────────
_BG = "#0d1117"
_CARD = "#141a23"
_CARD_LIGHTER = "#171f2a"
_CARD_BORDER = "#1c2735"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"
_ACCENT_SOFT = "#2563eb"
_GREEN = "#34d399"
_RED = "#ef4444"


# ══════════════════════════════════════════════════════════════════════════════
#  1. PAGE TRANSITION HELPER
# ══════════════════════════════════════════════════════════════════════════════

class PageTransitionHelper(QObject):
    """Manages fast, subtle (120ms) cross-fade transitions for QStackedWidget.
    
    Instantly cancels running animations if the user clicks rapidly to guarantee
    zero perceived lag.
    """

    def __init__(self, stack: QStackedWidget, duration_ms: int = 120, parent: QObject | None = None) -> None:
        super().__init__(parent or stack)
        self._stack = stack
        self._duration_ms = duration_ms
        self._anim: QVariantAnimation | None = None
        self._effect: QGraphicsOpacityEffect | None = None
        self._target_widget: QWidget | None = None

    def switch_to(self, index: int) -> None:
        """Switch to page index with a smooth 120ms fade-in."""
        if index < 0 or index >= self._stack.count():
            return

        if self._stack.currentIndex() == index:
            return

        # Cancel any ongoing animation and clean up previous effects immediately
        self._cleanup()

        self._target_widget = self._stack.widget(index)
        self._stack.setCurrentIndex(index)

        if not self._target_widget:
            return

        self._effect = QGraphicsOpacityEffect(self._target_widget)
        self._effect.setOpacity(0.0)
        self._target_widget.setGraphicsEffect(self._effect)

        anim = QVariantAnimation(self)
        anim.setDuration(self._duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_update(val: float) -> None:
            if self._effect:
                self._effect.setOpacity(val)

        def _on_finish() -> None:
            self._cleanup()

        anim.valueChanged.connect(_on_update)
        anim.finished.connect(_on_finish)
        self._anim = anim
        anim.start()

    def _cleanup(self) -> None:
        if self._anim is not None:
            try:
                self._anim.stop()
                self._anim.deleteLater()
            except Exception:
                pass
            self._anim = None

        if self._target_widget is not None:
            try:
                self._target_widget.setGraphicsEffect(None)
            except Exception:
                pass
            self._target_widget = None

        self._effect = None


# ══════════════════════════════════════════════════════════════════════════════
#  2. UNIFIED ANIMATED TOGGLE SWITCH
# ══════════════════════════════════════════════════════════════════════════════

class AnimatedToggleSwitch(QWidget):
    """Clean, animated toggle switch with 140ms physics and color interpolation.
    
    Replaces inconsistent switches across Timeline and Settings.
    """

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, on_toggled: Callable[[bool], None] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(40, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = checked
        self._thumb_position = 1.0 if checked else 0.0

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_anim_val)

        if on_toggled:
            self.toggled.connect(on_toggled)

    def is_checked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        self.set_checked(checked)

    def set_checked(self, checked: bool, animated: bool = True) -> None:
        if self._checked == checked:
            return
        self._checked = checked

        if animated:
            self._anim.stop()
            self._anim.setStartValue(self._thumb_position)
            self._anim.setEndValue(1.0 if checked else 0.0)
            self._anim.start()
        else:
            self._thumb_position = 1.0 if checked else 0.0
            self.update()

        self.toggled.emit(self._checked)

    def _on_anim_val(self, val: float) -> None:
        self._thumb_position = float(val)
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.set_checked(not self._checked, animated=True)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0, 0, self.width(), self.height())

        # Track colors blending
        c_bg_off = QColor("#1c2735")
        c_bg_on = QColor(_ACCENT)
        bg_color = self._blend_colors(c_bg_off, c_bg_on, self._thumb_position)

        c_border_off = QColor("#28394e")
        c_border_on = QColor(_ACCENT)
        border_color = self._blend_colors(c_border_off, c_border_on, self._thumb_position)

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.2))
        corner_r = rect.height() / 2
        painter.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6), corner_r, corner_r)

        # Thumb circle
        padding = 2.5
        radius = (rect.height() - padding * 2) / 2
        start_x = padding + radius
        end_x = rect.width() - padding - radius
        current_x = start_x + (end_x - start_x) * self._thumb_position

        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(current_x - radius, padding, radius * 2, radius * 2))
        painter.end()

    @staticmethod
    def _blend_colors(c1: QColor, c2: QColor, factor: float) -> QColor:
        f = max(0.0, min(1.0, factor))
        r = int(c1.red() + (c2.red() - c1.red()) * f)
        g = int(c1.green() + (c2.green() - c1.green()) * f)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * f)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * f)
        return QColor(r, g, b, a)


# ══════════════════════════════════════════════════════════════════════════════
#  3. CHART VALUE ANIMATOR
# ══════════════════════════════════════════════════════════════════════════════

class ChartValueAnimator(QObject):
    """Smoothly interpolates chart bar values from old to new values over 160ms.
    
    Prevents abrupt bar jumps on data refresh or date change.
    """

    def __init__(self, update_callback: Callable[[list[float]], None], duration_ms: int = 160, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._callback = update_callback
        self._duration_ms = duration_ms
        self._anim: QVariantAnimation | None = None
        self._old_values: list[float] = []
        self._target_values: list[float] = []

    def animate_to(self, new_values: list[float]) -> None:
        if not self._old_values:
            self._old_values = [0.0] * len(new_values)
            self._target_values = list(new_values)
            self._callback(new_values)
            return

        # Pad arrays if lengths differ
        max_len = max(len(self._old_values), len(new_values))
        old_v = self._old_values + [0.0] * (max_len - len(self._old_values))
        target_v = list(new_values) + [0.0] * (max_len - len(new_values))

        # Check if values actually changed
        if old_v == target_v:
            return

        if self._anim is not None:
            self._anim.stop()

        self._target_values = target_v

        anim = QVariantAnimation(self)
        anim.setDuration(self._duration_ms)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_step(progress: float) -> None:
            p = float(progress)
            interpolated = [
                old + (tgt - old) * p for old, tgt in zip(old_v, target_v)
            ]
            self._old_values = interpolated
            self._callback(interpolated)

        def _on_finish() -> None:
            self._old_values = target_v
            self._callback(target_v)

        anim.valueChanged.connect(_on_step)
        anim.finished.connect(_on_finish)
        self._anim = anim
        anim.start()


# ══════════════════════════════════════════════════════════════════════════════
#  4. IN-PLACE WIDGET RECYCLING HELPER
# ══════════════════════════════════════════════════════════════════════════════

TWidget = TypeVar("TWidget", bound=QWidget)
TData = TypeVar("TData")

def recycle_widgets_in_place(
    layout: QLayout,
    existing_widgets: list[TWidget],
    new_data: Sequence[TData],
    create_fn: Callable[[], TWidget],
    update_fn: Callable[[TWidget, TData, int], None],
) -> list[TWidget]:
    """Updates a list of widgets in-place inside a layout without deleteLater() thrash.
    
    - If new data has the same length, all existing widgets are reused.
    - If new data has more items, existing widgets are updated and new ones appended.
    - If new data has fewer items, existing widgets are updated and excess are hidden.
    """
    n_existing = len(existing_widgets)
    n_new = len(new_data)

    # Update existing widgets
    for i in range(min(n_existing, n_new)):
        w = existing_widgets[i]
        update_fn(w, new_data[i], i)
        w.setVisible(True)

    # Append new widgets if needed
    if n_new > n_existing:
        for i in range(n_existing, n_new):
            w = create_fn()
            update_fn(w, new_data[i], i)
            layout.addWidget(w)
            existing_widgets.append(w)
            w.setVisible(True)

    # Hide excess widgets
    elif n_new < n_existing:
        for i in range(n_new, n_existing):
            existing_widgets[i].setVisible(False)

    return existing_widgets
