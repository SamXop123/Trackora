"""Main dashboard window for the Trackora desktop application."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from trackora.charts import DailyUsageChart
from trackora.database.dashboard import DashboardRepository
from trackora.models.dashboard import DashboardSnapshot
from trackora.utils.formatting import format_duration_compact, format_last_refreshed
from trackora.widgets.active_status_card import ActiveStatusCard
from trackora.widgets.metric_card import MetricCard
from trackora.widgets.usage_table import UsageTableWidget


class DashboardWindow(QMainWindow):
    """Main Trackora dashboard UI."""

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
        metrics_layout.addWidget(self._top_app_card, 0, 1)
        metrics_layout.addWidget(self._refresh_card, 0, 2)
        metrics_layout.addWidget(self._active_status_card, 1, 0, 1, 3)
        outer.addLayout(metrics_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(18)

        self._chart = DailyUsageChart()
        self._chart.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self._wrap_section("Today's Usage Chart", self._chart))

        self._usage_table = UsageTableWidget()
        left_layout.addWidget(self._wrap_section("Top Apps Today", self._usage_table))
        content_layout.addWidget(left_panel, 3)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(18)

        self._top_apps_summary = QLabel("No tracked apps yet.")
        self._top_apps_summary.setObjectName("summaryLabel")
        self._top_apps_summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._top_apps_summary.setWordWrap(True)

        right_layout.addWidget(self._wrap_section("Today's Leaders", self._top_apps_summary))
        right_layout.addStretch(1)
        content_layout.addWidget(right_panel, 2)

        outer.addLayout(content_layout)

    def _wrap_section(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        container.setObjectName("sectionCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
