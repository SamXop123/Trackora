"""Settings control center — preferences, data management, and system integration."""

from __future__ import annotations

import os
import sys
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Any

from PySide6.QtCore import Qt, QTimer, QUrl, QSize, QVariantAnimation, QRectF
from PySide6.QtGui import QColor, QDesktopServices, QPixmap, QPainter, QBrush, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
    QAbstractButton,
)

from trackora.database.dashboard import DashboardRepository
from trackora.utils.settings import settings_manager
from trackora.utils.paths import default_database_path, default_state_path, get_asset_path
from trackora.window_state import read_window_state
from trackora.utils.time import now_utc
from trackora import __version__

_BG = "#0d1117"
_CARD = "#141a23"
_CARD_LIGHTER = "#171f2a"
_CARD_BORDER = "#1c2735"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"
_RED = "#ef4444"
_GREEN = "#34d399"
_ORANGE = "#f59e0b"

def _shadow(w: QWidget, blur: int = 15, op: int = 30, dy: int = 2) -> None:
    s = QGraphicsDropShadowEffect(w)
    s.setBlurRadius(blur)
    s.setColor(QColor(0, 0, 0, op))
    s.setOffset(0, dy)
    w.setGraphicsEffect(s)


class _Card(QFrame):
    def __init__(self, bg: str = _CARD, border: str = _CARD_BORDER, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"QFrame#dashCard {{ background:{bg}; border:1px solid {border}; border-radius:12px; }}"
        )
        _shadow(self)


class _ActionCard(QFrame):
    """A compact card acting as a dashboard button with smooth fade animations."""
    def __init__(self, title: str, icon: str = "", danger: bool = False, on_click: Callable | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._danger = danger
        self._on_click = on_click
        self._title = title
        self._icon = icon
        
        self._progress = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(0.0)
        self._anim.valueChanged.connect(self._update_progress)
        
        lo = QHBoxLayout(self)
        lo.setContentsMargins(16, 0, 16, 0)
        lo.setSpacing(12)
        
        if icon:
            self.i_lbl = QLabel(icon)
            self.i_lbl.setStyleSheet("background: transparent; border: none; font-size: 18px;")
            lo.addWidget(self.i_lbl)
            
        self.t_lbl = QLabel(title)
        self.t_lbl.setStyleSheet("background: transparent; border: none; font-size: 14px; font-weight: 600;")
        lo.addWidget(self.t_lbl, 1)
        
        _shadow(self, blur=12, op=25, dy=1)
        self._update_colors()

    def _update_progress(self, val: float) -> None:
        self._progress = val
        self.update()

    def enterEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def leaveEvent(self, event) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click()

    def _update_colors(self) -> None:
        if self._danger:
            c_text = QColor(_RED)
            c_icon = QColor(_RED)
        else:
            c_text = QColor(_TEXT_PRIMARY)
            c_icon = QColor(_ACCENT)
        if hasattr(self, "i_lbl"):
            self.i_lbl.setStyleSheet(f"color: {c_icon.name()}; background: transparent; border: none; font-size: 18px;")
        self.t_lbl.setStyleSheet(f"color: {c_text.name()}; background: transparent; border: none; font-size: 14px; font-weight: 600;")

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self._danger:
            c_bg_normal = QColor(239, 68, 68, 25)
            c_bg_hover = QColor(239, 68, 68, 51)
            c_border_normal = QColor(239, 68, 68, 102)
            c_border_hover = QColor(239, 68, 68, 153)
        else:
            c_bg_normal = QColor(_CARD)
            c_bg_hover = QColor(_CARD_LIGHTER)
            c_border_normal = QColor(_CARD_BORDER)
            c_border_hover = QColor(_ACCENT)
            
        p = self._progress
        bg = self._blend_colors(c_bg_normal, c_bg_hover, p)
        border = self._blend_colors(c_border_normal, c_border_hover, p)
        
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1.2))
        painter.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6), 12, 12)
        painter.end()

    def _blend_colors(self, c1: QColor, c2: QColor, factor: float) -> QColor:
        r = int(c1.red() + (c2.red() - c1.red()) * factor)
        g = int(c1.green() + (c2.green() - c1.green()) * factor)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * factor)
        return QColor(r, g, b, a)


class _FilterBtn(QWidget):
    """Horizontal navigation tab button with smooth fade transitions."""
    def __init__(self, text: str, cb: Callable, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active = False
        self._hovered = False
        self._text = text
        self._cb = cb
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        
        self._progress = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(0.0)
        self._anim.valueChanged.connect(self._update_progress)
        
        lo = QHBoxLayout(self)
        lo.setContentsMargins(18, 0, 18, 0)
        self._lbl = QLabel(text)
        self._lbl.setStyleSheet("color: transparent; font-size:13px; font-weight:600; background:transparent; border:none;")
        lo.addWidget(self._lbl)

    def _update_progress(self, val: float) -> None:
        self._progress = val
        self.update()

    def set_active(self, a: bool) -> None:
        if self._active == a:
            return
        self._active = a
        self._start_animation()

    def enterEvent(self, event) -> None:
        self._hovered = True
        self._start_animation()

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self._start_animation()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._cb(self._text)

    def _start_animation(self) -> None:
        target = 1.0 if self._active else (0.4 if self._hovered else 0.0)
        self._anim.stop()
        self._anim.setStartValue(self._progress)
        self._anim.setEndValue(target)
        self._anim.start()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        c_bg_normal = QColor(0, 0, 0, 0)
        c_bg_hover = QColor(_CARD_LIGHTER)
        c_bg_active = QColor(_ACCENT)
        
        c_border_normal = QColor(_CARD_BORDER)
        c_border_hover = QColor(_CARD_BORDER)
        c_border_active = QColor(_ACCENT)
        
        c_text_normal = QColor(_TEXT_SECONDARY)
        c_text_hover = QColor(_TEXT_PRIMARY)
        c_text_active = QColor("#ffffff")
        
        p = self._progress
        if p <= 0.4:
            t = p / 0.4
            bg = self._blend_colors(c_bg_normal, c_bg_hover, t)
            border = self._blend_colors(c_border_normal, c_border_hover, t)
            text = self._blend_colors(c_text_normal, c_text_hover, t)
        else:
            t = (p - 0.4) / 0.6
            bg = self._blend_colors(c_bg_hover, c_bg_active, t)
            border = self._blend_colors(c_border_hover, c_border_active, t)
            text = self._blend_colors(c_text_hover, c_text_active, t)
            
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)
        
        painter.setPen(text)
        font = self.font()
        font.setPointSizeF(9.5)
        font.setBold(True)
        font.setFamily("Inter")
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()

    def _blend_colors(self, c1: QColor, c2: QColor, factor: float) -> QColor:
        r = int(c1.red() + (c2.red() - c1.red()) * factor)
        g = int(c1.green() + (c2.green() - c1.green()) * factor)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * factor)
        return QColor(r, g, b, a)


class _KVRow(QWidget):
    """A dense key-value row inside a Control Center card."""
    def __init__(self, key: str, value: str = "—", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        lo = QHBoxLayout(self)
        lo.setContentsMargins(0, 0, 0, 0)
        
        self.k_lbl = QLabel(key)
        self.k_lbl.setFixedWidth(200)
        self.k_lbl.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 14px; font-weight: 500;")
        
        self.v_lbl = QLabel(value)
        self.v_lbl.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        
        lo.addWidget(self.k_lbl)
        lo.addWidget(self.v_lbl, 1)

    def set_value(self, value: str, color: str | None = None) -> None:
        self.v_lbl.setText(value)
        if color:
            self.v_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")


class _ControlRow(QWidget):
    """A dense key-control row for settings toggles."""
    def __init__(self, key: str, widget: QWidget, desc: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lo = QHBoxLayout(self)
        lo.setContentsMargins(0, 8, 0, 8)
        
        vlo = QVBoxLayout()
        vlo.setSpacing(2)
        
        k_lbl = QLabel(key)
        k_lbl.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        vlo.addWidget(k_lbl)
        
        if desc:
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
            d_lbl.setWordWrap(True)
            vlo.addWidget(d_lbl)
            
        lo.addLayout(vlo, 1)
        lo.addWidget(widget)


class _Switch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._thumb_position = 0.0
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(160)
        self._anim.valueChanged.connect(self._update_thumb)
        
    def sizeHint(self) -> QSize:
        return QSize(38, 20)
        
    def _update_thumb(self, val: float) -> None:
        self._thumb_position = val
        self.update()
        
    def setChecked(self, checked: bool) -> None:
        super().setChecked(checked)
        self._anim.stop()
        self._thumb_position = 1.0 if checked else 0.0
        self.update()
        
    def nextCheckState(self) -> None:
        super().nextCheckState()
        self._anim.stop()
        self._anim.setStartValue(self._thumb_position)
        self._anim.setEndValue(1.0 if self.isChecked() else 0.0)
        self._anim.start()
        
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        
        c_bg_unchecked = QColor(_CARD_LIGHTER)
        c_bg_checked = QColor(_ACCENT)
        bg_color = self._blend_colors(c_bg_unchecked, c_bg_checked, self._thumb_position)
        
        c_border_unchecked = QColor(_CARD_BORDER)
        c_border_checked = QColor(_ACCENT)
        border_color = self._blend_colors(c_border_unchecked, c_border_checked, self._thumb_position)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.2))
        painter.drawRoundedRect(rect.adjusted(0.6, 0.6, -0.6, -0.6), rect.height() / 2, rect.height() / 2)
        
        padding = 2.5
        radius = (rect.height() - padding * 2) / 2
        start_x = padding + radius
        end_x = rect.width() - padding - radius
        current_x = start_x + (end_x - start_x) * self._thumb_position
        
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(current_x - radius, padding, radius * 2, radius * 2))
        painter.end()

    def _blend_colors(self, c1: QColor, c2: QColor, factor: float) -> QColor:
        r = int(c1.red() + (c2.red() - c1.red()) * factor)
        g = int(c1.green() + (c2.green() - c1.green()) * factor)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * factor)
        a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * factor)
        return QColor(r, g, b, a)


def _create_switch(checked: bool, on_change: Callable) -> _Switch:
    s = _Switch()
    s.setChecked(checked)
    s.toggled.connect(on_change)
    return s


class _SegmentedControl(QWidget):
    """A horizontal segmented button group for selections with hover transitions."""
    def __init__(self, options: list[tuple[str, Any]], current_val: Any, on_change: Callable, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {_CARD_LIGHTER}; border: 1px solid {_CARD_BORDER}; border-radius: 8px;")
        
        lo = QHBoxLayout(self)
        lo.setContentsMargins(4, 4, 4, 4)
        lo.setSpacing(4)
        
        self.btns = []
        for text, val in options:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("val", val)
            
            if val == current_val:
                btn.setChecked(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {_CARD};
                        color: {_TEXT_PRIMARY};
                        border-radius: 6px;
                        font-weight: 600;
                        border: 1px solid {_CARD_BORDER};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {_TEXT_SECONDARY};
                        border: none;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.03);
                        color: {_TEXT_PRIMARY};
                        border-radius: 6px;
                    }}
                """)
                
            btn.clicked.connect(lambda checked, b=btn: self._on_btn_clicked(b, on_change))
            self.btns.append(btn)
            lo.addWidget(btn)

    def _on_btn_clicked(self, clicked_btn: QPushButton, on_change: Callable) -> None:
        for btn in self.btns:
            if btn == clicked_btn:
                btn.setChecked(True)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {_CARD};
                        color: {_TEXT_PRIMARY};
                        border-radius: 6px;
                        font-weight: 600;
                        border: 1px solid {_CARD_BORDER};
                    }}
                """)
                on_change(btn.property("val"))
            else:
                btn.setChecked(False)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {_TEXT_SECONDARY};
                        border: none;
                        font-weight: 500;
                    }}
                    QPushButton:hover {{
                        background: rgba(255, 255, 255, 0.03);
                        color: {_TEXT_PRIMARY};
                        border-radius: 6px;
                    }}
                """)


class SettingsPage(QWidget):
    """Application settings dashboard."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository: DashboardRepository | None = None
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_extension_status)
        self._build_layout()

    def set_repository(self, repo: DashboardRepository) -> None:
        self._repository = repo

    def refresh_data(self) -> None:
        self._refresh_data_tab()
        self._timer.start(1000)
        self._update_extension_status()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._timer.stop()

    def _build_layout(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(48, 48, 48, 48)
        main.setSpacing(24)

        # Header
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        t = QLabel("Settings")
        t.setStyleSheet(
            f"color:{_TEXT_PRIMARY}; font-size:22px; font-weight:700; background:transparent; border:none;"
        )
        hdr.addWidget(t)
        st = QLabel("Configure your tracking preferences and database options")
        st.setStyleSheet(
            f"color:{_TEXT_SECONDARY}; font-size:13px; background:transparent; border:none;"
        )
        hdr.addWidget(st)
        main.addLayout(hdr)

        # 1. Top Navigation Bar (Horizontal Tabs)
        nav_lo = QHBoxLayout()
        nav_lo.setSpacing(12)
        
        self.tabs = {}
        categories = ["General", "Tracking", "Data", "Advanced", "About"]
        for cat in categories:
            btn = _FilterBtn(cat, self._on_tab_clicked)
            self.tabs[cat] = btn
            nav_lo.addWidget(btn)
        nav_lo.addStretch(1)
        main.addLayout(nav_lo)

        # 2. Content Stack
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_general_tab())
        self._stack.addWidget(self._build_tracking_tab())
        self._stack.addWidget(self._build_data_tab())
        self._stack.addWidget(self._build_advanced_tab())
        self._stack.addWidget(self._build_about_tab())
        
        main.addWidget(self._stack, 1)
        
        # Select Tracking by default
        self._on_tab_clicked("Tracking")

    def _on_tab_clicked(self, category: str) -> None:
        for cat, btn in self.tabs.items():
            btn.set_active(cat == category)
            
        idx = list(self.tabs.keys()).index(category)
        widget = self._stack.widget(idx)
        self._stack.setCurrentIndex(idx)
        if widget is not None:
            self._fade_widget(widget)

    def _fade_widget(self, widget: QWidget) -> None:
        eff = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(eff)
        
        anim = QVariantAnimation(self)
        anim.setDuration(220)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(lambda val: eff.setOpacity(val))
        anim.finished.connect(lambda: widget.setGraphicsEffect(None))  # type: ignore
        anim.start()
        
        self._page_fade_anim = anim

    # ── TABS ─────────────────────────────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        card = _Card()
        clo = QVBoxLayout(card)
        clo.setContentsMargins(24, 16, 24, 16)
        clo.setSpacing(8)
        
        # Launch on Login (Windows only)
        import sys
        if sys.platform == "win32":
            from windows.startup import is_windows_startup_enabled, set_windows_startup
            clo.addWidget(_ControlRow("Launch on Login", 
                _create_switch(is_windows_startup_enabled(), set_windows_startup),
                "Start the background tracking daemon automatically when logging in."
            ))
            self._add_separator(clo)

        clo.addWidget(_ControlRow("Start Minimized", 
            _create_switch(settings_manager.get("start_minimized"), lambda c: settings_manager.set("start_minimized", c)),
            "Open the application in the background."
        ))
        self._add_separator(clo)
        
        clo.addWidget(_ControlRow("Notifications", 
            _create_switch(settings_manager.get("desktop_notifications"), lambda c: settings_manager.set("desktop_notifications", c)),
            "Show alerts for focus goals and system events."
        ))
        self._add_separator(clo)
        
        clo.addWidget(_ControlRow("Minimize to Tray", 
            _create_switch(settings_manager.get("minimize_to_tray"), lambda c: settings_manager.set("minimize_to_tray", c)),
            "Keep Trackora running when closing the window."
        ))

        lo.addWidget(card)
        lo.addStretch(1)
        return w

    def _add_separator(self, layout: QVBoxLayout) -> None:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_CARD_BORDER};")
        layout.addWidget(sep)

    def _build_tracking_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        # Primary Status Card
        card1 = _Card()
        clo1 = QVBoxLayout(card1)
        clo1.setContentsMargins(24, 20, 24, 20)
        clo1.setSpacing(0)
        
        self._kv_track = _KVRow("Tracking Status")
        self._kv_ext = _KVRow("Extension Status")
        self._kv_app = _KVRow("Current Application")
        self._kv_win = _KVRow("Current Window")
        self._kv_upd = _KVRow("Last Update")
        
        # Display current interval directly from settings manager
        val = settings_manager.get("tracking_interval_seconds")
        self._kv_int = _KVRow("Tracking Interval", f"{val} seconds")
        
        clo1.addWidget(self._kv_track)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_ext)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_app)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_win)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_upd)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_int)
        
        lo.addWidget(card1)

        # Secondary Controls Card
        card2 = _Card()
        clo2 = QVBoxLayout(card2)
        clo2.setContentsMargins(24, 16, 24, 16)
        
        intervals = [("1s", 1), ("3s", 3), ("5s", 5), ("10s", 10)]
        cur_val = settings_manager.get("tracking_interval_seconds")
        
        seg = _SegmentedControl(intervals, cur_val, self._on_interval_changed)
        seg.setFixedWidth(240)
        
        clo2.addWidget(_ControlRow("Polling Interval", seg, "Frequency at which the daemon fetches new window states."))
        
        lo.addWidget(card2)
        lo.addStretch(1)
        return w

    def _on_interval_changed(self, val: int) -> None:
        settings_manager.set("tracking_interval_seconds", val)
        self._kv_int.set_value(f"{val} seconds")

    def _update_extension_status(self) -> None:
        import sys
        if sys.platform == "win32":
            from windows.daemon import is_service_active_win
            daemon_active = is_service_active_win()
            if not daemon_active:
                self._kv_track.set_value("● Disconnected", _RED)
                self._kv_ext.set_value("● Disconnected", _RED)
                self._kv_app.set_value("—", _TEXT_MUTED)
                self._kv_win.set_value("—", _TEXT_MUTED)
                self._kv_upd.set_value("Daemon not running", _ORANGE)
                return

            from trackora.window_state import get_default_provider
            res = get_default_provider().get_window_state()
        else:
            res = read_window_state()

        state_path = default_state_path()
        now = time.time()
        last_mtime = 0

        if sys.platform == "win32":
            seconds_ago = 0 if (res.state is not None) else 60
        else:
            if state_path.exists():
                last_mtime = os.path.getmtime(state_path)
            seconds_ago = int(now - last_mtime)

        if res.error or not res.state or seconds_ago > 30:
            self._kv_track.set_value("● Disconnected", _RED)
            self._kv_ext.set_value("● Disconnected", _RED)
            self._kv_app.set_value("—", _TEXT_MUTED)
            self._kv_win.set_value("—", _TEXT_MUTED)
            
            if sys.platform == "win32":
                self._kv_upd.set_value(res.error or "No focused window", _ORANGE)
            else:
                if seconds_ago > 86400:
                    self._kv_upd.set_value("Long time ago", _TEXT_MUTED)
                else:
                    self._kv_upd.set_value(f"{seconds_ago} seconds ago", _ORANGE)
            return

        st = res.state
        self._kv_track.set_value("● Active", _GREEN)
        self._kv_ext.set_value("● Connected", _GREEN)
        self._kv_app.set_value(st.app)
        
        title = st.title
        if len(title) > 60:
            title = title[:57] + "..."
        self._kv_win.set_value(title)
        
        if sys.platform == "win32" or seconds_ago <= 1:
            self._kv_upd.set_value("Just now")
        else:
            self._kv_upd.set_value(f"{seconds_ago} seconds ago")

    def _build_data_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        # Stats Card
        card1 = _Card()
        clo1 = QVBoxLayout(card1)
        clo1.setContentsMargins(24, 20, 24, 20)
        clo1.setSpacing(0)
        
        self._kv_dbsize = _KVRow("Database Size")
        self._kv_dbsess = _KVRow("Total Sessions")
        self._kv_dbpath = _KVRow("Database Path", str(default_database_path()))
        self._kv_dbpath.v_lbl.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px; font-family: monospace;")
        self._kv_dbpath.v_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._kv_dbrange = _KVRow("Tracking Range")
        
        clo1.addWidget(self._kv_dbsize)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_dbsess)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_dbpath)
        self._add_separator(clo1)
        clo1.addWidget(self._kv_dbrange)
        
        lo.addWidget(card1)
        
        # Actions Layout
        act_lo = QHBoxLayout()
        act_lo.setSpacing(16)
        act_lo.addWidget(_ActionCard("Backup Database", "📥"))
        act_lo.addWidget(_ActionCard("Export JSON", "📤"))
        act_lo.addWidget(_ActionCard("Import JSON", "🔄"))
        
        open_folder = _ActionCard("Open Data Folder", "📂", on_click=lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(default_database_path().parent))))
        act_lo.addWidget(open_folder)
        
        lo.addLayout(act_lo)
        lo.addStretch(1)
        return w

    def _refresh_data_tab(self) -> None:
        if not self._repository: return
        try:
            stats = self._repository.get_database_stats()
            sess = stats.get("total_sessions", 0)
            sz = stats.get("size_bytes", 0) / 1024.0 / 1024.0
            
            e_dt = stats.get("earliest_date")
            l_dt = stats.get("latest_date")
            
            self._kv_dbsize.set_value(f"{sz:.2f} MB")
            self._kv_dbsess.set_value(f"{sess:,}")
            
            if e_dt and l_dt:
                self._kv_dbrange.set_value(f"{e_dt.strftime('%b %d, %Y')} — {l_dt.strftime('%b %d, %Y')}")
            else:
                self._kv_dbrange.set_value("No data available")
        except Exception:
            pass

    def _build_advanced_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        # Developer Options Card
        card1 = _Card()
        clo1 = QVBoxLayout(card1)
        clo1.setContentsMargins(24, 16, 24, 16)
        clo1.setSpacing(8)
        
        clo1.addWidget(_ControlRow("Debug Logging", 
            _create_switch(settings_manager.get("enable_debug_logging"), lambda c: settings_manager.set("enable_debug_logging", c)),
            "Write verbose output to standard logs."
        ))
        self._add_separator(clo1)
        
        clo1.addWidget(_ControlRow("Developer Info", 
            _create_switch(settings_manager.get("show_dev_info"), lambda c: settings_manager.set("show_dev_info", c)),
            "Display extra UI identifiers."
        ))
        self._add_separator(clo1)
        
        clo1.addWidget(_ControlRow("Auto Backup", 
            _create_switch(settings_manager.get("auto_backup_daily"), lambda c: settings_manager.set("auto_backup_daily", c)),
            "Automatically backup DB every 24 hours."
        ))
        lo.addWidget(card1)

        # Danger Zone
        d_lbl = QLabel("DANGER ZONE")
        d_lbl.setStyleSheet(f"color: {_RED}; font-size: 12px; font-weight: 700; letter-spacing: 0.1em;")
        lo.addWidget(d_lbl)

        d_lo = QHBoxLayout()
        d_lo.setSpacing(16)
        
        rt = _ActionCard("Reset Today's Data", "🗑️", danger=True, on_click=self._on_reset_today)
        ra = _ActionCard("Wipe Database Completely", "⚠️", danger=True, on_click=self._on_reset_all)
        d_lo.addWidget(rt)
        d_lo.addWidget(ra)
        
        lo.addLayout(d_lo)
        lo.addStretch(1)
        return w

    def _on_reset_today(self) -> None:
        if not self._repository: return
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            "Are you sure you want to delete all tracking data for today?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            now = now_utc()
            start_of_day_utc = datetime(now.year, now.month, now.day, tzinfo=now.tzinfo)
            self._repository.reset_today(start_of_day_utc)
            self._refresh_data_tab()

    def _on_reset_all(self) -> None:
        if not self._repository: return
        reply = QMessageBox.question(
            self, 'Confirm Wipe',
            "Are you ABSOLUTELY sure you want to wipe all tracking data forever?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repository.reset_all()
            self._refresh_data_tab()

    def _build_about_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        logo_lo = QHBoxLayout()
        logo_label = QLabel()
        logo_path = get_asset_path("trackora_logo.png")
        if logo_path.exists():
            px = QPixmap(str(logo_path))
            logo_label.setPixmap(px.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
        title = QLabel("Trackora")
        title.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 24px; font-weight: 800; letter-spacing: 0.05em;")
        
        logo_lo.addWidget(logo_label)
        logo_lo.addWidget(title)
        logo_lo.addStretch()
        lo.addLayout(logo_lo)

        card = _Card()
        clo = QVBoxLayout(card)
        clo.setContentsMargins(24, 20, 24, 20)
        clo.setSpacing(0)
        
        import sys
        is_win = (sys.platform == "win32")

        os_name = "Linux"
        try:
            if not is_win:
                with open("/etc/os-release") as f:
                    for line in f:
                        if line.startswith("PRETTY_NAME="):
                            os_name = line.split("=")[1].strip().strip('"')
                            break
            else:
                os_name = f"{platform.system()} {platform.release()}"
        except Exception:
            os_name = platform.system()
            
        clo.addWidget(_KVRow("Trackora Version", f"v{__version__}"))
        self._add_separator(clo)

        if is_win:
            clo.addWidget(_KVRow("Tracking Engine", "Win32 Native"))
        else:
            clo.addWidget(_KVRow("GNOME Version", "45+"))
            self._add_separator(clo)
            clo.addWidget(_KVRow("Extension Version", "v1"))

        self._add_separator(clo)
        clo.addWidget(_KVRow("Python Version", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"))
        self._add_separator(clo)
        clo.addWidget(_KVRow("Database Version", "v1"))
        self._add_separator(clo)
        clo.addWidget(_KVRow("Operating System", os_name))
        
        lo.addWidget(card)
        
        act_lo = QHBoxLayout()
        act_lo.setSpacing(16)
        btn_gh = _ActionCard("GitHub Repository", "🌐", on_click=lambda: QDesktopServices.openUrl(QUrl("https://github.com/trackora/trackora")))
        btn_docs = _ActionCard("Documentation", "📚", on_click=lambda: QDesktopServices.openUrl(QUrl("https://github.com/trackora/trackora")))
        act_lo.addWidget(btn_gh)
        act_lo.addWidget(btn_docs)
        
        lo.addLayout(act_lo)
        lo.addStretch(1)
        return w
