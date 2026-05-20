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
        self.setWindowTitle("Trackora Dashboard")
        self.resize(1220, 820)
        self.setMinimumSize(1040, 700)
        self._build_ui()
        self._apply_styles()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_dashboard)
        self._timer.start(self._refresh_seconds * 1000)
        self._active_tick_timer = QTimer(self)
        self._active_tick_timer.timeout.connect(self._active_status_card.tick)
        self._active_tick_timer.start(1000)
        self.refresh_dashboard()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        title = QLabel("Trackora")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Wayland-native activity dashboard for your current day")
        subtitle.setObjectName("subtitleLabel")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch(1)

        self._status_label = QLabel("Waiting for data…")
        self._status_label.setObjectName("statusLabel")
        header_layout.addWidget(self._status_label)

        outer.addLayout(header_layout)

        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(16)
        metrics_layout.setVerticalSpacing(16)

        self._total_today_card = MetricCard(
            title="Total Screen Time Today",
            value="0m",
            subtitle="Across all tracked apps",
        )
        self._yesterday_card = MetricCard(
            title="Yesterday",
            value="0m",
            subtitle="Previous day total",
        )
        self._last7days_card = MetricCard(
            title="Last 7 Days",
            value="0m",
            subtitle="Rolling total",
        )
        self._top_app_card = MetricCard(
            title="Top App Today",
            value="No data",
            subtitle="No usage recorded yet",
        )
        self._refresh_card = MetricCard(
            title="Last Refresh",
            value="Waiting…",
            subtitle="Dashboard auto-refresh",
        )
        self._active_status_card = ActiveStatusCard()

        metrics_layout.addWidget(self._total_today_card, 0, 0)
        metrics_layout.addWidget(self._yesterday_card, 0, 1)
        metrics_layout.addWidget(self._last7days_card, 0, 2)
        metrics_layout.addWidget(self._refresh_card, 0, 3)
        metrics_layout.addWidget(self._active_status_card, 1, 0, 1, 2)
        metrics_layout.addWidget(self._top_app_card, 1, 2, 1, 2)
        outer.addLayout(metrics_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(18)

        self._chart = DailyUsageChart()
        self._chart_section = self._wrap_section("Today's Usage Chart", self._chart)
        self._chart_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self._chart_section, 3)

        self._usage_table = UsageTableWidget()
        self._table_section = self._wrap_section("Top Apps Today", self._usage_table)
        left_layout.addWidget(self._table_section, 2)
        left_layout.setStretch(0, 3)
        left_layout.setStretch(1, 2)
        content_layout.addWidget(left_panel, 3)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(18)

        self._top_apps_summary = QLabel("No tracked apps yet.")
        self._top_apps_summary.setObjectName("summaryLabel")
        self._top_apps_summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._top_apps_summary.setWordWrap(True)

        self._weekly_chart = WeeklyUsageChart()
        right_layout.addWidget(self._wrap_section("Weekly Screen Time", self._weekly_chart), 2)
        right_layout.addWidget(self._wrap_section("Today's Leaders", self._top_apps_summary), 1)
        right_layout.setStretch(0, 2)
        right_layout.setStretch(1, 1)
        right_layout.addStretch(1)
        content_layout.addWidget(right_panel, 2)

        outer.addLayout(content_layout)

    def _wrap_section(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        container.setObjectName("sectionCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return container

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #0b0e12;
                color: #f3f7ff;
            }
            QLabel#subtitleLabel {
                color: #8ea1bd;
                font-size: 13px;
            }
            QLabel#statusLabel {
                background: #111821;
                border: 1px solid #1d2a39;
                border-radius: 10px;
                color: #a9bdd8;
                padding: 10px 14px;
                font-size: 12px;
            }
            QWidget#metricCard, QWidget#sectionCard {
                background: #111418;
                border: 1px solid #1c2430;
                border-radius: 18px;
            }
            QLabel#sectionTitle {
                color: #f3f7ff;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#summaryLabel {
                color: #d6ddea;
                font-size: 14px;
                line-height: 1.5;
            }
            QTableWidget {
                background: transparent;
                border: none;
                gridline-color: #1c2430;
                color: #f3f7ff;
                selection-background-color: #1e395f;
                selection-color: #f3f7ff;
            }
            QHeaderView::section {
                background: #0f1620;
                color: #8ea1bd;
                border: none;
                padding: 8px;
                font-weight: 600;
            }
            QTableCornerButton::section {
                background: #0f1620;
                border: none;
            }
            """
        )

    def refresh_dashboard(self) -> None:
        snapshot = self._repository.load_snapshot()
        self._render_snapshot(snapshot)

    def _render_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._status_label.setText(snapshot.status_message)
        self._total_today_card.set_content(
            value=format_duration_compact(snapshot.total_today_seconds),
            subtitle=f"{len(snapshot.all_apps)} apps tracked today",
        )
        self._yesterday_card.set_content(
            value=format_duration_compact(snapshot.total_yesterday_seconds),
            subtitle=format_duration_caption(snapshot.total_yesterday_seconds),
        )
        self._last7days_card.set_content(
            value=format_duration_compact(snapshot.total_last7days_seconds),
            subtitle=format_duration_caption(snapshot.total_last7days_seconds),
        )

        if snapshot.top_apps:
            leader = snapshot.top_apps[0]
            self._top_app_card.set_content(
                value=leader.app_name,
                subtitle=format_duration_caption(leader.duration_seconds),
            )
        else:
            self._top_app_card.set_content(
                value="No data",
                subtitle="Open a few apps to start seeing usage",
            )

        self._refresh_card.set_content(
            value=format_last_refreshed(snapshot.last_refreshed),
            subtitle=f"Auto-refresh every {self._refresh_seconds}s",
        )
        self._active_status_card.update_status(snapshot.active_app)
        self._usage_table.set_rows(snapshot.all_apps)
        self._chart.update_chart(snapshot.hourly_labels, snapshot.hourly_values)
        self._weekly_chart.update_chart(snapshot.weekly_labels, snapshot.weekly_values)
        self._top_apps_summary.setText(self._build_summary_text(snapshot))

    def _build_summary_text(self, snapshot: DashboardSnapshot) -> str:
        if not snapshot.top_apps:
            return "No tracked app sessions yet today. Once the background tracker records activity, your leaders will appear here."

        lines = []
        for index, item in enumerate(snapshot.top_apps[:3], start=1):
            lines.append(
                f"{index}. {item.app_name}  •  {format_duration_compact(item.duration_seconds)}"
            )

        if snapshot.active_app is not None:
            lines.append("")
            lines.append(
                "Active now: "
                f"{snapshot.active_app.app_name}  •  "
                f"{format_duration_compact(snapshot.active_app.elapsed_seconds)}"
            )

        if snapshot.weekly_days:
            strongest_day = max(snapshot.weekly_days, key=lambda item: item.duration_seconds)
            lines.append("")
            lines.append(
                "Strongest day: "
                f"{strongest_day.day.strftime('%a %d %b')}  •  "
                f"{format_duration_compact(strongest_day.duration_seconds)}"
            )

        return "\n".join(lines)
