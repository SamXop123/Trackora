"""Main application window for Trackora.

Architecture
------------
MainWindow
├── _Sidebar          — vertical navigation rail with icons
└── QStackedWidget    — page container
    ├── [0] DashboardPage
    ├── [1] TimelinePage
    ├── [2] ApplicationsPage
    ├── [3] InsightsPage
    ├── [4] GoalsPage
    ├── [5] ReportsPage
    └── [6] SettingsPage

Backend wiring (preserved)
--------------------------
- DashboardRepository(database_path).load_snapshot()
    → called every `refresh_seconds` via QTimer
    → forwarded to DashboardPage.refresh(snapshot)
- 1-second tick timer → DashboardPage.tick_active_session()
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from trackora.database.dashboard import DashboardRepository
from trackora.gui.pages import (
    ApplicationsPage,
    DashboardPage,
    GoalsPage,
    InsightsPage,
    ReportsPage,
    SettingsPage,
    TimelinePage,
)


# ── Color tokens ─────────────────────────────────────────────────────────────
_BG = "#0d1117"
_SIDEBAR_BG = "#0f1419"
_SIDEBAR_BORDER = "#1a2332"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#5a6a80"
_ACCENT = "#3b82f6"
_NAV_ACTIVE_BG = "#172135"
_NAV_HOVER_BG = "#141e2d"


# ── Navigation definitions (label, icon character) ──────────────────────────

_NAV_ITEMS: list[tuple[str, str]] = [
    ("Dashboard",     "⌂"),
    ("Timeline",      "◔"),
    ("Applications",  "⊞"),
    ("Insights",      "◈"),
    ("Goals",         "◎"),
    ("Reports",       "◷"),
]


class _NavButton(QWidget):
    """Single sidebar navigation item with icon + label."""

    def __init__(
        self,
        text: str,
        icon_char: str,
        index: int,
        callback,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._index = index
        self._callback = callback
        self._active = False
        self._hovered = False
        self.setFixedHeight(40)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        self._icon = QLabel(icon_char)
        self._icon.setFixedWidth(20)
        self._icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        layout.addWidget(self._label)
        layout.addStretch(1)

        self._apply_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_style()

    def _apply_style(self) -> None:
        bg = "transparent"
        text_color = _TEXT_SECONDARY
        icon_color = _TEXT_MUTED

        if self._active:
            bg = _NAV_ACTIVE_BG
            text_color = _TEXT_PRIMARY
            icon_color = _ACCENT
        elif self._hovered:
            bg = _NAV_HOVER_BG
            text_color = _TEXT_PRIMARY
            icon_color = _TEXT_SECONDARY

        self.setStyleSheet(f"background: {bg}; border-radius: 10px;")
        self._icon.setStyleSheet(f"color: {icon_color}; font-size: 15px; background: transparent; border: none;")
        self._label.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 500; background: transparent; border: none;")

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()

    def mousePressEvent(self, event):
        self._callback(self._index)


class _Sidebar(QWidget):
    """Vertical navigation sidebar matching the reference design."""

    def __init__(self, navigate_callback, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(190)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setStyleSheet(
            f"background: {_SIDEBAR_BG}; border-right: 1px solid {_SIDEBAR_BORDER};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # ── Branding ─────────────────────────────────────────────────────
        brand_row = QHBoxLayout()
        brand_row.setSpacing(8)
        brand_row.setContentsMargins(8, 0, 0, 0)

        brand_icon = QLabel("◉")
        brand_icon.setStyleSheet(f"color: {_ACCENT}; font-size: 20px; background: transparent; border: none;")
        brand_row.addWidget(brand_icon)

        brand_text = QLabel("Trackora")
        brand_text.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 16px; font-weight: 700; background: transparent; border: none;")
        brand_row.addWidget(brand_text)
        brand_row.addStretch(1)

        layout.addLayout(brand_row)
        layout.addSpacing(20)

        # ── Navigation items ─────────────────────────────────────────────
        self._buttons: list[_NavButton] = []
        for i, (label, icon) in enumerate(_NAV_ITEMS):
            btn = _NavButton(label, icon, i, navigate_callback)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        # ── Quote section ────────────────────────────────────────────────
        quote_frame = QWidget()
        quote_frame.setStyleSheet(
            f"background: transparent; border: none;"
        )
        quote_layout = QVBoxLayout(quote_frame)
        quote_layout.setContentsMargins(12, 0, 12, 0)
        quote_layout.setSpacing(6)

        quote_mark = QLabel("❝")
        quote_mark.setStyleSheet(f"color: {_ACCENT}; font-size: 24px; background: transparent; border: none;")
        quote_layout.addWidget(quote_mark)

        quote_text = QLabel("Focus is the\nfoundation of\nmeaningful progress.")
        quote_text.setWordWrap(True)
        quote_text.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px; line-height: 1.5; background: transparent; border: none;")
        quote_layout.addWidget(quote_text)

        layout.addWidget(quote_frame)
        layout.addSpacing(12)

        # ── Settings button ──────────────────────────────────────────────
        settings_btn = _NavButton("Settings", "⚙", len(_NAV_ITEMS), navigate_callback)
        self._buttons.append(settings_btn)
        layout.addWidget(settings_btn)

        # Set initial active
        self.set_active(0)

    def set_active(self, index: int) -> None:
        for btn in self._buttons:
            btn.set_active(btn._index == index)


class MainWindow(QMainWindow):
    """Top-level Trackora application window."""

    def __init__(self, *, database_path: Path, refresh_seconds: int) -> None:
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

    # ── Layout construction ───────────────────────────────────────────────

    def _build_layout(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        self._sidebar = _Sidebar(self._on_nav_click)
        root_layout.addWidget(self._sidebar)

        # Page stack
        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack, 1)

        # Pages (order matches _NAV_ITEMS + Settings)
        self._dashboard_page = DashboardPage()
        self._stack.addWidget(self._dashboard_page)     # 0
        self._stack.addWidget(TimelinePage())            # 1
        self._stack.addWidget(ApplicationsPage())        # 2
        self._stack.addWidget(InsightsPage())            # 3
        self._stack.addWidget(GoalsPage())               # 4
        self._stack.addWidget(ReportsPage())             # 5
        self._stack.addWidget(SettingsPage())            # 6

        self._stack.setCurrentIndex(0)

    # ── Navigation ────────────────────────────────────────────────────────

    def _on_nav_click(self, index: int) -> None:
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._sidebar.set_active(index)

    # ── Timers ────────────────────────────────────────────────────────────

    def _start_timers(self) -> None:
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(self._refresh_seconds * 1000)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._dashboard_page.tick_active_session)
        self._tick_timer.start(1000)

    # ── Data refresh ─────────────────────────────────────────────────────

    def _refresh_dashboard(self) -> None:
        snapshot = self._repository.load_snapshot()
        self._dashboard_page.refresh(snapshot)

    # ── Base styling ─────────────────────────────────────────────────────

    def _apply_base_style(self) -> None:
        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background: {_BG};
                color: {_TEXT_PRIMARY};
                font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif;
            }}
            """
        )
