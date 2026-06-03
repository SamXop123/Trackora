"""Settings page — preferences, data management, and system integration."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QSize
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPixmap, QCursor
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from trackora.database.dashboard import DashboardRepository
from trackora.utils.settings import settings_manager
from trackora.utils.paths import trackora_data_dir, default_database_path
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

def _shadow(w: QWidget, blur: int = 20, op: int = 35, dy: int = 3) -> None:
    s = QGraphicsDropShadowEffect(w)
    s.setBlurRadius(blur)
    s.setColor(QColor(0, 0, 0, op))
    s.setOffset(0, dy)
    w.setGraphicsEffect(s)


class _Card(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"QFrame#settingsCard {{ background:{_CARD}; border:1px solid {_CARD_BORDER}; border-radius:14px; }}"
        )
        _shadow(self)


class _SidebarButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(40)
        self.setCheckable(True)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_TEXT_SECONDARY};
                border: none;
                border-radius: 8px;
                text-align: left;
                padding-left: 16px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {_CARD_LIGHTER};
                color: {_TEXT_PRIMARY};
            }}
            QPushButton:checked {{
                background: rgba(59, 130, 246, 0.15);
                color: {_ACCENT};
                font-weight: 700;
            }}
        """)


class _Button(QPushButton):
    def __init__(self, text: str, danger: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        bg = _RED if danger else _CARD_LIGHTER
        hover = "#dc2626" if danger else _CARD_BORDER
        text_col = "#ffffff" if danger else _TEXT_PRIMARY
        
        border = "none" if danger else f"1px solid {_CARD_BORDER}"
        
        self.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {text_col};
                border: {border};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: {hover};
            }}
        """)


def _create_checkbox(text: str, desc: str, checked: bool, on_change) -> QWidget:
    w = QWidget()
    lo = QVBoxLayout(w)
    lo.setContentsMargins(0, 0, 0, 0)
    lo.setSpacing(4)
    
    cb = QCheckBox(text)
    cb.setChecked(checked)
    cb.toggled.connect(on_change)
    cb.setStyleSheet(f"""
        QCheckBox {{ color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 500; spacing: 10px; }}
        QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 1px solid {_CARD_BORDER}; background: {_CARD_LIGHTER}; }}
        QCheckBox::indicator:checked {{ background: {_ACCENT}; border: 1px solid {_ACCENT}; }}
    """)
    lo.addWidget(cb)
    
    lbl = QLabel(desc)
    lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px; margin-left: 28px;")
    lo.addWidget(lbl)
    return w


def _create_radio(text: str, value: int, group: QButtonGroup) -> QRadioButton:
    rb = QRadioButton(text)
    rb.setProperty("val", value)
    rb.setStyleSheet(f"""
        QRadioButton {{ color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 500; spacing: 10px; }}
        QRadioButton::indicator {{ width: 18px; height: 18px; border-radius: 9px; border: 1px solid {_CARD_BORDER}; background: {_CARD_LIGHTER}; }}
        QRadioButton::indicator:checked {{ background: {_ACCENT}; border: 1px solid {_ACCENT}; }}
    """)
    group.addButton(rb)
    return rb


class SettingsPage(QWidget):
    """Application settings and data management."""

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
        self._timer.start(2000)
        self._update_extension_status()

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._timer.stop()

    def _build_layout(self) -> None:
        main = QHBoxLayout(self)
        main.setContentsMargins(40, 40, 40, 40)
        main.setSpacing(40)

        # 1. Sidebar (Left)
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        side_lo = QVBoxLayout(sidebar)
        side_lo.setContentsMargins(0, 0, 0, 0)
        side_lo.setSpacing(8)

        lbl = QLabel("SETTINGS")
        lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; padding-left: 16px;")
        side_lo.addWidget(lbl)
        side_lo.addSpacing(4)

        self._btn_group = QButtonGroup(self)
        self._btn_group.setExclusive(True)
        
        categories = ["General", "Tracking", "Data", "Advanced", "About"]
        for i, cat in enumerate(categories):
            btn = _SidebarButton(cat)
            self._btn_group.addButton(btn, i)
            side_lo.addWidget(btn)
            if i == 0:
                btn.setChecked(True)
                
        self._btn_group.idClicked.connect(self._on_category_changed)
        side_lo.addStretch(1)
        main.addWidget(sidebar)

        # 2. Content Stack (Right)
        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_general_tab())
        self._stack.addWidget(self._build_tracking_tab())
        self._stack.addWidget(self._build_data_tab())
        self._stack.addWidget(self._build_advanced_tab())
        self._stack.addWidget(self._build_about_tab())
        
        main.addWidget(self._stack, 1)

    def _on_category_changed(self, idx: int) -> None:
        self._stack.setCurrentIndex(idx)

    # ── TABS ─────────────────────────────────────────────────────────────────

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        t = QLabel("General Settings")
        t.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        lo.addWidget(t)

        card = _Card()
        clo = QVBoxLayout(card)
        clo.setContentsMargins(24, 24, 24, 24)
        clo.setSpacing(20)

        clo.addWidget(_create_checkbox(
            "Launch Trackora on Login",
            "Automatically start tracking when you log into your desktop.",
            settings_manager.get("launch_on_login"),
            lambda c: settings_manager.set("launch_on_login", c)
        ))
        
        clo.addWidget(_create_checkbox(
            "Start Minimized",
            "Open the application in the background without showing the dashboard.",
            settings_manager.get("start_minimized"),
            lambda c: settings_manager.set("start_minimized", c)
        ))
        
        clo.addWidget(_create_checkbox(
            "Enable Desktop Notifications",
            "Show alerts for focus goals and system events.",
            settings_manager.get("desktop_notifications"),
            lambda c: settings_manager.set("desktop_notifications", c)
        ))
        
        clo.addWidget(_create_checkbox(
            "Minimize to Tray when Closed",
            "Keep Trackora running in the system tray when closing the window.",
            settings_manager.get("minimize_to_tray"),
            lambda c: settings_manager.set("minimize_to_tray", c)
        ))

        lo.addWidget(card)
        lo.addStretch(1)
        return w

    def _build_tracking_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        t = QLabel("Tracking & Integrations")
        t.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        lo.addWidget(t)

        # Interval
        card1 = _Card()
        c1lo = QVBoxLayout(card1)
        c1lo.setContentsMargins(24, 20, 24, 20)
        c1lo.setSpacing(12)
        
        l1 = QLabel("Tracking Interval")
        l1.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 600; background: transparent; border: none;")
        c1lo.addWidget(l1)
        
        rlo = QVBoxLayout()
        rlo.setSpacing(8)
        self._interval_group = QButtonGroup(self)
        
        intervals = [1, 3, 5, 10]
        cur_val = settings_manager.get("tracking_interval_seconds")
        for val in intervals:
            rb = _create_radio(f"{val} second{'s' if val > 1 else ''}", val, self._interval_group)
            if val == cur_val: rb.setChecked(True)
            rlo.addWidget(rb)
        
        self._interval_group.idToggled.connect(self._on_interval_changed)
        c1lo.addLayout(rlo)
        
        s1 = QLabel("Lower intervals increase accuracy but use slightly more resources.")
        s1.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        c1lo.addWidget(s1)
        lo.addWidget(card1)

        # GNOME Extension Status
        card2 = _Card()
        c2lo = QVBoxLayout(card2)
        c2lo.setContentsMargins(24, 20, 24, 20)
        c2lo.setSpacing(16)
        
        l2 = QLabel("GNOME Extension Status")
        l2.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 600; background: transparent; border: none;")
        c2lo.addWidget(l2)
        
        self._ext_status = QLabel("Checking...")
        self._ext_status.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; font-weight: 700;")
        c2lo.addWidget(self._ext_status)
        
        self._ext_app = QLabel("Current App: —")
        self._ext_app.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px;")
        c2lo.addWidget(self._ext_app)
        
        self._ext_title = QLabel("Window Title: —")
        self._ext_title.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px;")
        c2lo.addWidget(self._ext_title)
        
        lo.addWidget(card2)
        lo.addStretch(1)
        return w

    def _on_interval_changed(self, rb, checked):
        if checked:
            val = rb.property("val")
            settings_manager.set("tracking_interval_seconds", val)

    def _update_extension_status(self) -> None:
        res = read_window_state()
        if res.error or not res.state:
            self._ext_status.setText("● Disconnected")
            self._ext_status.setStyleSheet(f"color: {_RED}; font-size: 13px; font-weight: 700;")
            self._ext_app.setText("Current App: —")
            self._ext_title.setText("Window Title: —")
            return
            
        st = res.state
        self._ext_status.setText("● Connected")
        self._ext_status.setStyleSheet(f"color: {_GREEN}; font-size: 13px; font-weight: 700;")
        self._ext_app.setText(f"Current App: {st.app}")
        self._ext_title.setText(f"Window Title: {st.title}")

    def _build_data_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        t = QLabel("Data Management")
        t.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        lo.addWidget(t)

        # Path Card
        card1 = _Card()
        c1lo = QVBoxLayout(card1)
        c1lo.setContentsMargins(24, 20, 24, 20)
        c1lo.setSpacing(8)
        
        db_path = default_database_path()
        l1 = QLabel("Database Path")
        l1.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        c1lo.addWidget(l1)
        
        p = QLabel(str(db_path))
        p.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px; font-family: monospace; background: {_CARD_LIGHTER}; padding: 8px; border-radius: 6px;")
        p.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        c1lo.addWidget(p)
        
        btn_lo = QHBoxLayout()
        btn_lo.setSpacing(12)
        btn_lo.addWidget(_Button("Create Backup"))
        btn_lo.addWidget(_Button("Export Database"))
        btn_lo.addWidget(_Button("Import Database"))
        
        open_btn = _Button("Open Data Folder")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(db_path.parent))))
        btn_lo.addWidget(open_btn)
        
        btn_lo.addStretch(1)
        c1lo.addSpacing(8)
        c1lo.addLayout(btn_lo)
        lo.addWidget(card1)

        # Stats Card
        card2 = _Card()
        self.c2lo = QVBoxLayout(card2)
        self.c2lo.setContentsMargins(24, 20, 24, 20)
        self.c2lo.setSpacing(12)
        
        l2 = QLabel("Database Statistics")
        l2.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
        self.c2lo.addWidget(l2)
        
        self._db_stats = [
            QLabel("Total Sessions Stored: —"),
            QLabel("Database Size: —"),
            QLabel("Earliest Tracking Date: —"),
            QLabel("Latest Tracking Date: —")
        ]
        for lbl in self._db_stats:
            lbl.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px;")
            self.c2lo.addWidget(lbl)
            
        lo.addWidget(card2)
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
            
            e_str = e_dt.strftime("%Y-%m-%d %H:%M") if e_dt else "—"
            l_str = l_dt.strftime("%Y-%m-%d %H:%M") if l_dt else "—"
            
            self._db_stats[0].setText(f"Total Sessions Stored: {sess:,}")
            self._db_stats[1].setText(f"Database Size: {sz:.2f} MB")
            self._db_stats[2].setText(f"Earliest Tracking Date: {e_str}")
            self._db_stats[3].setText(f"Latest Tracking Date: {l_str}")
        except Exception:
            pass

    def _build_advanced_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(24)

        t = QLabel("Advanced Options")
        t.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 24px; font-weight: 700; background: transparent; border: none;")
        lo.addWidget(t)

        card1 = _Card()
        c1lo = QVBoxLayout(card1)
        c1lo.setContentsMargins(24, 24, 24, 24)
        c1lo.setSpacing(20)
        
        c1lo.addWidget(_create_checkbox(
            "Enable Debug Logging",
            "Write verbose diagnostic output to log files.",
            settings_manager.get("enable_debug_logging"),
            lambda c: settings_manager.set("enable_debug_logging", c)
        ))
        
        c1lo.addWidget(_create_checkbox(
            "Show Developer Information",
            "Display extra identifiers and IDs in the UI.",
            settings_manager.get("show_dev_info"),
            lambda c: settings_manager.set("show_dev_info", c)
        ))
        
        c1lo.addWidget(_create_checkbox(
            "Auto Backup Database Daily",
            "Automatically back up your telemetry database every 24 hours.",
            settings_manager.get("auto_backup_daily"),
            lambda c: settings_manager.set("auto_backup_daily", c)
        ))
        lo.addWidget(card1)

        # Danger Zone
        d_lbl = QLabel("Danger Zone")
        d_lbl.setStyleSheet(f"color: {_RED}; font-size: 14px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase;")
        lo.addWidget(d_lbl)

        card2 = _Card()
        card2.setStyleSheet(
            f"QFrame#settingsCard {{ background:{_CARD}; border:1px solid rgba(239, 68, 68, 0.3); border-radius:14px; }}"
        )
        c2lo = QVBoxLayout(card2)
        c2lo.setContentsMargins(24, 20, 24, 20)
        c2lo.setSpacing(12)
        
        btn_reset_today = _Button("Reset Today's Data", danger=True)
        btn_reset_today.setFixedWidth(200)
        btn_reset_today.clicked.connect(self._on_reset_today)
        c2lo.addWidget(btn_reset_today)
        
        lbl_rt = QLabel("Permanently delete all tracking sessions recorded since midnight.")
        lbl_rt.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px; margin-bottom: 8px;")
        c2lo.addWidget(lbl_rt)
        
        btn_reset_all = _Button("Reset All Tracking Data", danger=True)
        btn_reset_all.setFixedWidth(200)
        btn_reset_all.clicked.connect(self._on_reset_all)
        c2lo.addWidget(btn_reset_all)
        
        lbl_ra = QLabel("Wipe the database completely. This action cannot be undone.")
        lbl_ra.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px;")
        c2lo.addWidget(lbl_ra)
        
        lo.addWidget(card2)
        lo.addStretch(1)
        return w

    def _on_reset_today(self) -> None:
        if not self._repository: return
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            "Are you sure you want to delete all tracking data for today? This cannot be undone.",
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
            "Are you ABSOLUTELY sure you want to wipe all tracking data forever? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._repository.reset_all()
            self._refresh_data_tab()

    def _build_about_tab(self) -> QWidget:
        w = QWidget()
        lo = QVBoxLayout(w)
        lo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.setContentsMargins(0, 0, 0, 0)
        lo.setSpacing(20)

        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = Path(__file__).resolve().parents[3] / "assets" / "trackora_logo.png"
        if logo_path.exists():
            px = QPixmap(str(logo_path))
            logo_label.setPixmap(px.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lo.addWidget(logo_label)

        title = QLabel("Trackora")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 28px; font-weight: 800; letter-spacing: 0.05em;")
        lo.addWidget(title)

        card = _Card()
        card.setFixedWidth(400)
        clo = QVBoxLayout(card)
        clo.setContentsMargins(24, 24, 24, 24)
        clo.setSpacing(12)
        
        info = [
            ("Application Version", "1.0.0"),
            ("Database Version", "v1"),
            ("GNOME Version", "45+"),
            ("Operating System", "Linux"),
        ]
        
        for k, v in info:
            r = QHBoxLayout()
            kl = QLabel(k)
            kl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; font-weight: 500;")
            vl = QLabel(v)
            vl.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 600;")
            r.addWidget(kl)
            r.addStretch(1)
            r.addWidget(vl)
            clo.addLayout(r)
            
        lo.addWidget(card)
        
        btn_lo = QHBoxLayout()
        btn_lo.setSpacing(16)
        
        btn_gh = _Button("Open GitHub Repository")
        btn_gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/trackora/trackora")))
        btn_lo.addWidget(btn_gh)
        
        btn_docs = _Button("Documentation")
        btn_docs.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/trackora/trackora")))
        btn_lo.addWidget(btn_docs)
        
        lo.addLayout(btn_lo)
        lo.addStretch(1)
        return w
