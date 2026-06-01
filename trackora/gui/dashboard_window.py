"""Main application window for Trackora.

Architecture: MainWindow → _Sidebar + QStackedWidget[pages]
Backend wiring: DashboardRepository → QTimer → DashboardPage.refresh/tick
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QMainWindow, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from trackora.database.dashboard import DashboardRepository
from trackora.gui.pages import (
    ApplicationsPage, DashboardPage, GoalsPage,
    InsightsPage, ReportsPage, SettingsPage, TimelinePage,
)

# ── Color tokens ─────────────────────────────────────────────────────────────
_BG = "#0d1117"
_SIDEBAR_BG = "#0f1419"
_SIDEBAR_BORDER = "#1a2332"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"
_NAV_ACTIVE_BG = "#152035"
_NAV_HOVER_BG = "#121b28"

# ── Navigation definitions ──────────────────────────────────────────────────
_NAV_ITEMS: list[tuple[str, str]] = [
    ("Dashboard",    "⌂"),
    ("Timeline",     "◔"),
    ("Applications", "⊞"),
    ("Insights",     "◈"),
    ("Goals",        "◎"),
    ("Reports",      "◷"),
]


class _NavButton(QWidget):
    """Sidebar navigation item with icon, label, active indicator, and hover."""

    def __init__(self, text: str, icon_char: str, index: int, callback, parent=None):
        super().__init__(parent)
        self._index = index
        self._callback = callback
        self._active = False
        self._hovered = False
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(11)

        self._icon = QLabel(icon_char)
        self._icon.setFixedWidth(18)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        layout.addWidget(self._label)
        layout.addStretch(1)
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            bg, text_c, icon_c = _NAV_ACTIVE_BG, _TEXT_PRIMARY, _ACCENT
        elif self._hovered:
            bg, text_c, icon_c = _NAV_HOVER_BG, _TEXT_PRIMARY, _TEXT_SECONDARY
        else:
            bg, text_c, icon_c = "transparent", _TEXT_SECONDARY, _TEXT_MUTED

        self.setStyleSheet(f"background: {bg}; border-radius: 9px;")
        self._icon.setStyleSheet(
            f"color: {icon_c}; font-size: 14px; background: transparent; border: none;"
        )
        self._label.setStyleSheet(
            f"color: {text_c}; font-size: 13px; font-weight: 500; "
            f"background: transparent; border: none;"
        )

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._active:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(QColor(_ACCENT)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(2, 10, 3, self.height() - 20), 1.5, 1.5)
            painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()

    def mousePressEvent(self, event):
        self._callback(self._index)


class _Sidebar(QWidget):
    """Vertical navigation sidebar."""

    def __init__(self, navigate_callback, parent=None):
        super().__init__(parent)
        self.setFixedWidth(185)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet(
            f"background: {_SIDEBAR_BG}; border-right: 1px solid {_SIDEBAR_BORDER};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 18, 10, 14)
        layout.setSpacing(3)

        # Branding
        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_row.setContentsMargins(8, 0, 0, 0)

        brand_icon = QLabel("◉")
        brand_icon.setStyleSheet(
            f"color: {_ACCENT}; font-size: 18px; background: transparent; border: none;"
        )
        brand_row.addWidget(brand_icon)

        brand_text = QLabel("Trackora")
        brand_text.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        brand_row.addWidget(brand_text)
        brand_row.addStretch(1)
        layout.addLayout(brand_row)
        layout.addSpacing(22)

        # Nav items
        self._buttons: list[_NavButton] = []
        for i, (label, icon) in enumerate(_NAV_ITEMS):
            btn = _NavButton(label, icon, i, navigate_callback)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        # Quote
        quote_frame = QWidget()
        quote_frame.setStyleSheet("background: transparent; border: none;")
        ql = QVBoxLayout(quote_frame)
        ql.setContentsMargins(10, 0, 10, 0)
        ql.setSpacing(5)

        qm = QLabel("❝")
        qm.setStyleSheet(
            f"color: {_ACCENT}; font-size: 20px; background: transparent; border: none;"
        )
        ql.addWidget(qm)

        qt = QLabel("Focus is the\nfoundation of\nmeaningful progress.")
        qt.setWordWrap(True)
        qt.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; background: transparent; border: none;"
        )
        ql.addWidget(qt)
        layout.addWidget(quote_frame)
        layout.addSpacing(10)

        # Settings
        settings_btn = _NavButton("Settings", "⚙", len(_NAV_ITEMS), navigate_callback)
        self._buttons.append(settings_btn)
        layout.addWidget(settings_btn)
        self.set_active(0)

    def set_active(self, index: int):
        for btn in self._buttons:
            btn.set_active(btn._index == index)


class MainWindow(QMainWindow):
    """Top-level Trackora application window."""

    def __init__(self, *, database_path: Path, refresh_seconds: int):
        super().__init__()
        self._repository = DashboardRepository(database_path)
        self._refresh_seconds = refresh_seconds

        self.setWindowTitle("Trackora")
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        self._build_layout()
        self._apply_base_style()
        self._start_timers()
        self._refresh_dashboard()

    def _build_layout(self):
        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = _Sidebar(self._on_nav_click)
        root_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack, 1)

        self._dashboard_page = DashboardPage()
        self._dashboard_page.set_repository(self._repository)
        self._stack.addWidget(self._dashboard_page)      # 0
        self._timeline_page = TimelinePage()
        self._timeline_page.set_repository(self._repository)
        self._stack.addWidget(self._timeline_page)            # 1
        self._apps_page = ApplicationsPage()
        self._apps_page.set_repository(self._repository)
        self._stack.addWidget(self._apps_page)            # 2
        self._insights_page = InsightsPage()
        self._insights_page.set_repository(self._repository)
        self._stack.addWidget(self._insights_page)        # 3
        self._stack.addWidget(GoalsPage())                # 4
        self._reports_page = ReportsPage()
        self._reports_page.set_repository(self._repository)
        self._stack.addWidget(self._reports_page)          # 5
        self._stack.addWidget(SettingsPage())             # 6
        self._stack.setCurrentIndex(0)

    def _on_nav_click(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._sidebar.set_active(index)
            # Refresh page data when navigating
            if index == 1:
                self._timeline_page.refresh_data()
            elif index == 2:
                self._apps_page.refresh_data()
            elif index == 3:
                self._insights_page.refresh_data()
            elif index == 5:
                self._reports_page.refresh_data()

    def _start_timers(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(self._refresh_seconds * 1000)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._dashboard_page.tick_active_session)
        self._tick_timer.start(1000)

    def _refresh_dashboard(self):
        from trackora.utils.logging import log_info, log_error
        log_info("dashboard refresh started")
        try:
            snapshot = self._repository.load_snapshot()
            self._dashboard_page.refresh(snapshot)
            # Also refresh timeline/apps page if currently visible
            if self._stack.currentIndex() == 1:
                self._timeline_page.refresh_data()
            elif self._stack.currentIndex() == 2:
                self._apps_page.refresh_data()
            elif self._stack.currentIndex() == 3:
                self._insights_page.refresh_data()
            elif self._stack.currentIndex() == 5:
                self._reports_page.refresh_data()
            log_info("dashboard refresh success")
        except Exception as exc:
            log_error(f"refresh exception if any: {exc}")

    def _apply_base_style(self):
        self.setStyleSheet(
            f"QMainWindow, QWidget {{ background: {_BG}; color: {_TEXT_PRIMARY}; "
            f"font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif; }}"
        )
