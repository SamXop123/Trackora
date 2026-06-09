"""Settings control center — preferences, data management, and system integration."""

from __future__ import annotations

import os
import sys
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Any

from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QColor, QDesktopServices, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from trackora.database.dashboard import DashboardRepository
from trackora.utils.settings import settings_manager
from trackora.utils.paths import trackora_data_dir, default_database_path, default_state_path
from trackora.window_state import read_window_state
from trackora.utils.time import now_utc

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


class _ActionCard(_Card):
    """A compact card acting as a dashboard button."""
    def __init__(self, title: str, icon: str = "", danger: bool = False, on_click: Callable = None, parent: QWidget | None = None) -> None:
        bg = _CARD if not danger else "rgba(239, 68, 68, 0.1)"
        border = _CARD_BORDER if not danger else "rgba(239, 68, 68, 0.4)"
        super().__init__(bg=bg, border=border, parent=parent)
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._danger = danger
        self._on_click = on_click
        
        lo = QHBoxLayout(self)
        lo.setContentsMargins(16, 0, 16, 0)
        lo.setSpacing(12)
        
        if icon:
            i_lbl = QLabel(icon)
            color = _RED if danger else _ACCENT
            i_lbl.setStyleSheet(f"color: {color}; font-size: 18px;")
            lo.addWidget(i_lbl)
            
        t_lbl = QLabel(title)
        color = _RED if danger else _TEXT_PRIMARY
        t_lbl.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: 600;")
        lo.addWidget(t_lbl, 1)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._on_click:
            self._on_click()
            
    def enterEvent(self, event) -> None:
        bg = "rgba(239, 68, 68, 0.2)" if self._danger else _CARD_LIGHTER
        border = "rgba(239, 68, 68, 0.6)" if self._danger else _ACCENT
        self.setStyleSheet(f"QFrame#dashCard {{ background:{bg}; border:1px solid {border}; border-radius:12px; }}")

    def leaveEvent(self, event) -> None:
        bg = "rgba(239, 68, 68, 0.1)" if self._danger else _CARD
        border = "rgba(239, 68, 68, 0.4)" if self._danger else _CARD_BORDER
        self.setStyleSheet(f"QFrame#dashCard {{ background:{bg}; border:1px solid {border}; border-radius:12px; }}")


class _FilterBtn(QWidget):
    """Horizontal navigation tab button."""
    def __init__(self, text: str, cb: Callable, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active = False
        self._text = text
        self._cb = cb
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        lo = QHBoxLayout(self)
        lo.setContentsMargins(16, 0, 16, 0)
        self._lbl = QLabel(text)
        lo.addWidget(self._lbl)
        self._apply_style()

    def _apply_style(self) -> None:
        bg = _ACCENT if self._active else "transparent"
        fg = "#ffffff" if self._active else _TEXT_SECONDARY
        bd = f"1px solid {_ACCENT}" if self._active else f"1px solid {_CARD_BORDER}"
        self._lbl.setStyleSheet(f"color:{fg}; font-size:13px; font-weight:600; background:transparent; border:none;")
        self.setStyleSheet(f"background:{bg}; border:{bd}; border-radius:8px;")

    def set_active(self, a: bool) -> None:
        self._active = a
        self._apply_style()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self._cb(self._text)


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

    def set_value(self, value: str, color: str = None) -> None:
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


def _create_switch(checked: bool, on_change: Callable) -> QCheckBox:
    cb = QCheckBox()
    cb.setChecked(checked)
    cb.toggled.connect(on_change)
    cb.setCursor(Qt.CursorShape.PointingHandCursor)
    cb.setStyleSheet(f"""
        QCheckBox::indicator {{ width: 36px; height: 20px; border-radius: 10px; border: 1px solid {_CARD_BORDER}; background: {_CARD_LIGHTER}; }}
        QCheckBox::indicator:checked {{ background: {_ACCENT}; border: 1px solid {_ACCENT}; }}
    """)
    return cb


class _SegmentedControl(QWidget):
    """A horizontal segmented button group for selections."""
    def __init__(self, options: list[tuple[str, Any]], current_val: Any, on_change: Callable, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet(f"background: {_CARD_LIGHTER}; border: 1px solid {_CARD_BORDER}; border-radius: 8px;")
        
        lo = QHBoxLayout(self)
        lo.setContentsMargins(4, 4, 4, 4)
        lo.setSpacing(2)
        
        self.btns = []
        for text, val in options:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("val", val)
            
            if val == current_val:
                btn.setChecked(True)
                btn.setStyleSheet(f"background: {_CARD}; color: {_TEXT_PRIMARY}; border-radius: 6px; font-weight: 600; border: 1px solid {_CARD_BORDER};")
            else:
                btn.setStyleSheet(f"background: transparent; color: {_TEXT_SECONDARY}; border: none; font-weight: 500;")
                
            btn.clicked.connect(lambda checked, b=btn: self._on_btn_clicked(b, on_change))
            self.btns.append(btn)
            lo.addWidget(btn)

    def _on_btn_clicked(self, clicked_btn: QPushButton, on_change: Callable) -> None:
        for btn in self.btns:
            if btn == clicked_btn:
                btn.setChecked(True)
                btn.setStyleSheet(f"background: {_CARD}; color: {_TEXT_PRIMARY}; border-radius: 6px; font-weight: 600; border: 1px solid {_CARD_BORDER};")
                on_change(btn.property("val"))
            else:
                btn.setChecked(False)
                btn.setStyleSheet(f"background: transparent; color: {_TEXT_SECONDARY}; border: none; font-weight: 500;")


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
        self._stack.setCurrentIndex(idx)

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
        
        # 'Launch on Login' removed: automatic startup is no longer supported.
        
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
        res = read_window_state()
        state_path = default_state_path()
        
        now = time.time()
        last_mtime = 0
        if state_path.exists():
            last_mtime = os.path.getmtime(state_path)
            
        seconds_ago = int(now - last_mtime)
        
        if res.error or not res.state or seconds_ago > 30:
            self._kv_track.set_value("● Disconnected", _RED)
            self._kv_ext.set_value("● Disconnected", _RED)
            self._kv_app.set_value("—", _TEXT_MUTED)
            self._kv_win.set_value("—", _TEXT_MUTED)
            
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
        
        if seconds_ago <= 1:
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
        logo_path = Path(__file__).resolve().parents[3] / "assets" / "trackora_logo.png"
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
        
        os_name = "Linux"
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        os_name = line.split("=")[1].strip().strip('"')
                        break
        except Exception:
            os_name = platform.system()
            
        clo.addWidget(_KVRow("Trackora Version", "v1.0.0"))
        self._add_separator(clo)
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
